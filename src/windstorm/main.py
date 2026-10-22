import json
import logging
import os
import shutil

logger = logging.getLogger("windstorm")

import fire

from windstorm.common.functions import setup_logging
from windstorm.common.api import verify_tool
from windstorm.common.sysml import init_variables, template_files
from windstorm.common.export_adapter import adapt
from windstorm.common.local_store import ElementStore
from windstorm.common.windtrader_jar import batch_export


def _collect_source_files(source_dir: str):
    """Recursively find ``.export.json`` and ``.sysml`` files under source_dir.

    Returns ``(export_files, sysml_files)`` as sorted lists of absolute paths,
    scanning subdirectories (nested Defias repos like
    ``models/``, ``requirements/``, ``verification/``). Symlinked directories
    are NOT followed (would risk cycles); they are logged at DEBUG so a
    symlinked ``models/`` -> ``../shared-models/`` is never silently invisible.
    """
    export_files = []
    sysml_files = []
    for dir_path, dir_names, file_names in os.walk(source_dir):
        for dir_name in dir_names:
            full_dir = os.path.join(dir_path, dir_name)
            if os.path.islink(full_dir):
                logger.debug(
                    "Skipping symlinked directory (not followed): %s", full_dir
                )
        for name in file_names:
            full = os.path.join(dir_path, name)
            if name.endswith(".export.json"):
                export_files.append(full)
            elif name.endswith(".sysml"):
                sysml_files.append(full)
    return sorted(export_files), sorted(sysml_files)


def _file_mtime(path):
    """Return the mtime_ns of ``path`` or None if it does not exist."""
    try:
        return os.stat(path).st_mtime_ns
    except OSError:
        return None


def _load_local_store(
    source_dir: str,
    dump_export_json: str = "",
    skip_export_errors: bool = False,
    exports_only: bool = False,
):
    """Build an offline ElementStore from .sysml / .export.json in a directory.

    Recursively scans ``source_dir`` (including subdirectories). Sources and
    already-exported JSON are treated as *complementary*, not exclusive:

      - ``*.export.json`` files are adapted directly.
      - Raw ``.sysml`` files are exported via the windtrader-java JAR
        (``batch-export`` writes ``<path>.export.json`` next to each source).
        A ``.sysml`` whose export is missing OR still not newer than
        (<=) the source is
        re-exported; a fresh export is reused (so an edit to a model is not
        silently ignored on the next run). Pass ``exports_only=True`` to
        trust the existing exports and never invoke Java.
      - ``dump_export_json``: after exporting, copy ALL loaded
        ``*.export.json`` files into this directory (mirroring the relative
        tree) so they can be reused directly — the fast, Java-free path.

    Raises ``RuntimeError`` for unusable toolchains and empty results; a
    single unexportable ``.sysml`` aborts unless ``skip_export_errors=True``
    (then it is skipped with a warning).

    Returns a populated ``ElementStore`` (API-shaped graph keyed by @id).
    """
    store = ElementStore()

    source_dir = os.path.abspath(source_dir)
    if not os.path.isdir(source_dir):
        raise RuntimeError("--source is not a directory: {}".format(source_dir))

    dump_dir = os.path.abspath(dump_export_json) if dump_export_json else ""
    if dump_export_json:
        # A dump dir nested under --source would be re-ingested on the next
        # run as an unchecked standalone export (B-2). Reject it outright, and
        # do it up front so bad flag combinations fail in milliseconds. Use
        # realpath so a symlinked dump dir pointing inside --source can't
        # bypass the guard (nit, round 3).
        try:
            common = os.path.commonpath(
                [os.path.realpath(source_dir), os.path.realpath(dump_dir)]
            )
        except ValueError:
            # Cross-drive paths (e.g. C:\models vs D:\dumps on Windows) are
            # definitionally outside --source; allow.
            common = ""
        if common == os.path.realpath(source_dir):
            raise RuntimeError(
                "--dump-export-json must point OUTSIDE --source "
                "(would be re-ingested on the next run): {} is under {}".format(
                    dump_dir, source_dir
                )
            )

    export_files, sysml_files = _collect_source_files(source_dir)

    if dump_export_json and not sysml_files:
        raise RuntimeError(
            "--dump-export-json requires --source pointing at raw .sysml files; "
            "there were no .sysml files under {}".format(source_dir)
        )

    # Which .sysml files need (re-)exporting: missing or stale export.
    # exports_only=True trusts existing exports and never asks for Java.
    need_export = []
    for path in sysml_files:
        out = path + ".export.json"
        export_mtime = _file_mtime(out)
        sysml_mtime = _file_mtime(path)
        if (not exports_only) and (
            export_mtime is None
            or (sysml_mtime is not None and export_mtime <= sysml_mtime)
        ):
            need_export.append(path)
        elif export_mtime is None:
            need_export.append(path)

    produced = []
    if need_export:
        if exports_only:
            # exports_only + missing exports: nothing to trust -> skip with a
            # warning rather than silently rendering a partial graph.
            logger.warning(
                "--exports-only set but %d .sysml file(s) have no export JSON; "
                "they will be skipped: %s",
                len(need_export),
                ", ".join(os.path.relpath(p, source_dir) for p in need_export[:5]),
            )
        else:
            logger.info(
                "Exporting {} .sysml file(s) (missing/stale export).".format(
                    len(need_export)
                )
            )
            # The jar writes <path>.export.json next to each source — make
            # sure we tell the user WHY when a read-only tree blocks that
            # write.
            unwritable = [
                os.path.dirname(p)
                for p in need_export
                if not os.access(os.path.dirname(p), os.W_OK)
            ]
            if unwritable:
                raise RuntimeError(
                    "--source tree is not writable; windtrader writes "
                    "<path>.export.json next to each .sysml.\n"
                    "  First unwritable dir(s): {}\n"
                    "  Make the tree writable or pre-export (see --dump-export-json "
                    "for an output dir outside --source).".format(
                        sorted(set(unwritable))[:3]
                    )
                )
            try:
                produced = batch_export(need_export)
            except RuntimeError as e:
                # Only skip a PER-FILE batch failure: distinguish it from a
                # toolchain preflight error (java not found, Java < 21,
                # WINDTRADER_JAR unset, jar missing) — a missing JVM must NOT
                # be swallowed and exit 0 with a partial graph (NB-A, round 4).
                # batch_export attaches .produced (the successful outputs) to
                # the batch-failure exception; preflight errors never do.
                if skip_export_errors and hasattr(e, "produced"):
                    partial = e.produced or []
                    logger.warning(
                        "Skipping export errors: %s (%d output(s) kept)",
                        e,
                        len(partial),
                    )
                    produced = partial
                else:
                    raise

    if need_export and not exports_only:
        # Any .sysml in this batch whose export was not freshly produced are
        # about to be loaded from a STALE export (or skipped). A present-but-
        # unrefreshed file is the round-3-blessed "jar skipped an already
        # current file" state -> INFO; only a genuinely ABSENT export gets the
        # WARNING (NB-B round 4 + round-5 refinement).
        produced_abs = {os.path.abspath(x) for x in produced}
        for p in need_export:
            if os.path.abspath(p + ".export.json") not in produced_abs:
                if os.path.exists(p + ".export.json"):
                    logger.info(
                        "Export for %s was not refreshed this run; its export "
                        "is still not newer than the source, so rendered "
                        "output may be stale.",
                        p,
                    )
                else:
                    logger.warning(
                        "No export for %s was produced this run; skipping this "
                        "file (missing export).",
                        p,
                    )

    # Adapt the union: standalone .export.json files + freshly produced exports.
    # Don't double-count a .sysml's export that was produced and also present as
    # a standalone file (they are the same file path).
    adapt_paths = []
    seen = set()
    for path in export_files:
        key = os.path.normcase(path)
        adapt_paths.append(path)
        seen.add(key)
    for out in produced:
        lo = os.path.normcase(os.path.abspath(out))
        if lo not in seen:
            adapt_paths.append(out)
            seen.add(lo)

    for path in adapt_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                adapted = adapt(json.load(f))
        except (
            OSError,
            ValueError,
            AttributeError,
            TypeError,
            KeyError,
        ) as e:
            raise RuntimeError(
                "Failed to load export JSON from {}: {}".format(path, e)
            ) from e
        if len(adapted) == 0:
            logger.warning("Export JSON contributed 0 elements: %s", path)
        for eid, payload in adapted.items():
            existing = store.get(eid)
            if existing is not None and existing != payload:
                logger.warning(
                    "Duplicate @id %s supplied by %s differs from an "
                    "already-loaded element; last writer wins (sorted file "
                    "order). This can silently render stale data.",
                    eid,
                    path,
                )
        store.extend(adapted)
    logger.info(
        "Loaded {} export JSON file(s) -> {} element(s).".format(
            len(adapt_paths), len(store)
        )
    )

    # Dump exports for this run (mirroring the relative tree so nested subdir
    # collisions are avoided). Dump EVERY export we loaded, not just the ones
    # re-generated this run — otherwise a warm run yields a partial bundle
    # that renders a silently incomplete graph on the next --source dumps/.
    # (The requires-.sysml check ran up front; dump_dir is the abspath.)
    if dump_export_json:
        os.makedirs(dump_dir, exist_ok=True)
        dumped = 0
        dumped_from = sorted(set(adapt_paths))
        for out in dumped_from:
            rel = os.path.relpath(out, source_dir)
            dst = os.path.join(dump_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(out, dst)
            dumped += 1
        logger.info("Dumped {} export JSON file(s) to {}.".format(dumped, dump_dir))

    if len(store) == 0:
        if not sysml_files and not export_files:
            raise RuntimeError(
                "No .export.json or .sysml files found under {}".format(source_dir)
            )
        if exports_only:
            raise RuntimeError(
                "--exports-only set but no .export.json files with elements "
                "were found under {}.".format(source_dir)
            )
        if export_files and not sysml_files:
            # An exports-only tree that adapts to zero elements (NB-C, round 4).
            raise RuntimeError(
                "No elements could be loaded from the .export.json files under "
                "{} (none contained elements; check the files or the export "
                "bundle).".format(source_dir)
            )
        raise RuntimeError(
            "No elements could be exported from the .sysml under {}. Either "
            "the export toolchain failed (check WINDTRADER_JAR / java) or the "
            "files exported no elements.".format(source_dir)
        )

    logger.info("Local store built with {} element(s).".format(len(store)))
    return store


def windstorm(
    element_name: str,
    api: str = "http://sysml2-dev.intercax.com:9000",
    source: str = "",
    dump_export_json: str = "",
    exports_only: bool = False,
    skip_export_errors: bool = False,
    insecure: bool = False,
    project_id: str = "",
    element_type: str = "AnalysisCaseDefinition",
    in_directory: str = ".",
    out_directory: str = ".",
    graph_templates: bool = False,
    force_render_error_continue: bool = False,
    debug: bool = False,
):
    """
    This is a description of the program.

    Args:
        element_name: The analysis element to render.
        api: Live SysMLv2 API address (ignored when --source is set).
        source: Directory of local .sysml / .export.json files to render from
            instead of a live API. NOTE: for raw .sysml files, windstorm runs
            the windtrader-java JAR, which writes ``<path>.export.json`` next
            to each source (the source tree must be writable; add
            ``*.export.json`` to .gitignore if the tree is a git checkout).
        dump_export_json: When set with --source and raw .sysml files, copy the
            generated .export.json files into this directory (mirroring the
            relative tree) so they can be used directly on future runs
            (Java-free, fully offline). Requires --source with .sysml files
            and must point OUTSIDE --source.
        exports_only: With --source, trust the existing .export.json files and
            never invoke Java. .sysml files with a MISSING export are skipped
            with a warning; a STALE export is trusted as-is (no re-check).
        skip_export_errors: With --source, if the Java export batch reports a
            per-file failure, keep the outputs that succeeded and skip the
            failed .sysml files with a warning instead of aborting the whole
            run. Toolchain failures (java missing, WINDTRADER_JAR unset) are
            NOT swallowed — they abort.
    """
    setup_logging(debug)

    api_store = None
    if source:
        # Offline mode: build an ElementStore from local files and run the
        # exact same templating core against it (no network).
        api_store = _load_local_store(
            source,
            dump_export_json=dump_export_json,
            exports_only=exports_only,
            skip_export_errors=skip_export_errors,
        )
        project, aj = verify_tool(api_store, "", element_type, element_name, insecure)
    else:
        project, aj = verify_tool(api, project_id, element_type, element_name, insecure)

    if len(aj) == 0:
        if in_directory == out_directory:
            logger.info("Nothing to do, closing...")
        else:
            logger.info("Copying all files from input to output, no changes...")
            shutil.copytree(in_directory, out_directory, dirs_exist_ok=True)
    else:
        output = init_variables(api_store if source else api, project, aj)
        template_files(in_directory, out_directory, output, force_render_error_continue)


def main():
    """This function uses Fire to generate a command-line interface"""
    fire.Fire(windstorm)


if __name__ == "__main__":
    main()
