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

    Recursively scans ``source_dir`` (including subdirectories). Three layouts:
      - Already-exported JSON: ``*.export.json`` files are adapted directly.
      - Raw ``.sysml``: each file is exported via the windtrader-java JAR
        (``batch-export`` writes ``<path>.export.json`` next to the source),
        then adapted. Requires ``WINDTRADER_JAR``; see the preflight error.
      - ``dump_export_json``: after a raw ``.sysml`` export, copy the generated
        ``*.export.json`` files into this directory so they can be reused
        directly (the fast, Java-free, fully-offline path).

    Returns a populated ``ElementStore`` (API-shaped graph keyed by @id).
    """
    store = ElementStore()

    export_files, sysml_files = _collect_source_files(source_dir)

    if export_files:
        for path in export_files:
            with open(path, "r") as f:
                adapted = adapt(json.load(f))
            store.extend(adapted)
        logger.info(
            "Loaded {} export JSON file(s) -> {} element(s).".format(
                len(export_files), len(store._elements)
            )
        )
    elif sysml_files:
        # No exports yet: run the windtrader jar's batch-export over ALL files in
        # a single JVM invocation. It writes <path>.export.json next to each
        # source, so the exports persist and are reused on the next run.
        produced = batch_export(sysml_files)

        if dump_export_json:
            import shutil

            os.makedirs(dump_export_json, exist_ok=True)
            for out in produced:
                shutil.copy2(out, dump_export_json)
            logger.info(
                "Dumped {} export JSON file(s) to {}.".format(
                    len(produced), dump_export_json
                )
            )

        for out in produced:
            with open(out, "r") as f:
                store.extend(adapt(json.load(f)))

        if len(store._elements) == 0:
            raise RuntimeError(
                "No elements could be exported from .sysml under {}. "
                "Check WINDTRADER_JAR and the .sysml files.".format(source_dir)
            )
    else:
        raise RuntimeError(
            "No .export.json or .sysml files found under {}".format(source_dir)
        )

    logger.info("Local store built with {} element(s).".format(len(store._elements)))
    return store


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
            instead of a live API.
        dump_export_json: When set with --source and raw .sysml files, copy the
            generated .export.json files into this directory so they can be used
            directly on future runs (Java-free, fully offline).
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
