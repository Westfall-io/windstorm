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
    ``models/``, ``requirements/``, ``verification/``).
    """
    export_files = []
    sysml_files = []
    for dir_path, _dir_names, file_names in os.walk(source_dir):
        for name in file_names:
            full = os.path.join(dir_path, name)
            if name.endswith(".export.json"):
                export_files.append(full)
            elif name.endswith(".sysml"):
                sysml_files.append(full)
    return sorted(export_files), sorted(sysml_files)


def _load_local_store(source_dir: str, dump_export_json: str = ""):
    """Build an offline ElementStore from .sysml / .export.json in a directory.

    Recursively scans ``source_dir`` (including subdirectories). Sources and
    already-exported JSON are treated as *complementary*, not exclusive:

      - ``*.export.json`` files are adapted directly.
      - Raw ``.sysml`` files are exported via the windtrader-java JAR
        (``batch-export`` writes ``<path>.export.json`` next to each source).
        A ``.sysml`` whose export is missing OR older than the source is
        re-exported; a fresh export is reused (so an edit to a model is not
        silently ignored on the next run).
      - ``dump_export_json``: after exporting, copy the generated
        ``*.export.json`` files into this directory (mirroring the relative
        tree) so they can be reused directly — the fast, Java-free path.

    Returns a populated ``ElementStore`` (API-shaped graph keyed by @id).
    """
    store = ElementStore()

    source_dir = os.path.abspath(source_dir)
    export_files, sysml_files = _collect_source_files(source_dir)

    # Which .sysml files need (re-)exporting: missing or stale export.
    need_export = []
    for path in sysml_files:
        out = path + ".export.json"
        export_mtime = _file_mtime(out)
        sysml_mtime = _file_mtime(path)
        if export_mtime is None or (
            sysml_mtime is not None and export_mtime < sysml_mtime
        ):
            need_export.append(path)

    produced = []
    if need_export:
        logger.info(
            "Exporting {} .sysml file(s) (missing/stale export).".format(len(need_export))
        )
        produced = batch_export(need_export)

    # Adapt the union: standalone .export.json files + freshly produced exports.
    # Don't double-count a .sysml's export that was produced and also present as
    # a standalone file (they are the same file path).
    adapt_paths = []
    seen = set()
    for path in export_files:
        lo = path.lower()
        if lo not in seen:
            adapt_paths.append(path)
            seen.add(lo)
    for out in produced:
        lo = os.path.abspath(out).lower()
        if lo not in seen:
            adapt_paths.append(out)
            seen.add(lo)

    for path in adapt_paths:
        with open(path, "r") as f:
            adapted = adapt(json.load(f))
        store.extend(adapted)
    logger.info(
        "Loaded {} export JSON file(s) -> {} element(s).".format(
            len(adapt_paths), len(store._elements)
        )
    )

    # Dump the generated exports for this run (only after a raw .sysml export),
    # mirroring the relative tree so nested subdir collisions are avoided.
    if dump_export_json:
        if not sysml_files:
            raise RuntimeError(
                "--dump-export-json requires --source pointing at raw .sysml files; "
                "there were no .sysml files under {}".format(source_dir)
            )
        if not produced:
            logger.info(
                "No exports were generated this run (all .sysml exports fresh); "
                "nothing to dump to {}.".format(dump_export_json)
            )
        else:
            os.makedirs(dump_export_json, exist_ok=True)
            dumped = 0
            for out in produced:
                rel = os.path.relpath(out, source_dir)
                dst = os.path.join(dump_export_json, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(out, dst)
                dumped += 1
            logger.info("Dumped {} export JSON file(s) to {}.".format(dumped, dump_export_json))

    if len(store._elements) == 0:
        raise RuntimeError(
            "No elements could be exported from .sysml under {}. "
            "Check WINDTRADER_JAR and the .sysml files.".format(source_dir)
        )

    logger.info("Local store built with {} element(s).".format(len(store._elements)))
    return store


def _file_mtime(path):
    """Return the mtime of ``path`` or None if it does not exist."""
    try:
        return os.stat(path).st_mtime
    except OSError:
        return None


def windstorm(
    element_name: str,
    api: str = "http://sysml2-dev.intercax.com:9000",
    source: str = "",
    dump_export_json: str = "",
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
            (Java-free, fully offline). Requires --source with .sysml files.
    """
    setup_logging(debug)

    api_store = None
    if source:
        # Offline mode: build an ElementStore from local files and run the
        # exact same templating core against it (no network).
        api_store = _load_local_store(source, dump_export_json)
        project, aj = verify_tool(api_store, "", element_type, element_name, insecure)
    else:
        project, aj = verify_tool(api, project_id, element_type, element_name, insecure)

    if len(aj) == 0:
        if in_directory == out_directory:
            logger.info("Nothing to do, closing...")
        else:
            logger.info("Copying all files from input to output, no changes...")
            import shutil

            shutil.copytree(in_directory, out_directory, dirs_exist_ok=True)
    else:
        output = init_variables(api_store if source else api, project, aj)
        template_files(in_directory, out_directory, output, force_render_error_continue)


def main():
    """This function uses Fire to generate a command-line interface"""
    fire.Fire(windstorm)


if __name__ == "__main__":
    main()
