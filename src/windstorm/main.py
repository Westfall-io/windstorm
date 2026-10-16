import logging

logger = logging.getLogger("windstorm")

import fire

from windstorm.common.functions import setup_logging
from windstorm.common.api import verify_tool
from windstorm.common.sysml import init_variables, template_files


def _load_local_store(source_dir: str):
    """Build an offline ElementStore from .sysml / .export.json in a directory.

    Two supported layouts:
      - Already-exported JSON: ``*.export.json`` files are adapted directly.
      - Raw ``.sysml``: each file is exported via the windtrader-java JAR, then
        adapted. Requires the ``windtrader`` wrapper + JAR on PATH.

    Returns a populated ``ElementStore`` (API-shaped graph keyed by @id), or
    raises an informative error if nothing usable is found.
    """
    import glob
    import json
    import os
    import subprocess
    import tempfile

    from windstorm.common.export_adapter import adapt
    from windstorm.common.local_store import ElementStore

    store = ElementStore()

    export_files = sorted(glob.glob(os.path.join(source_dir, "*.export.json")))
    sysml_files = sorted(glob.glob(os.path.join(source_dir, "*.sysml")))

    if export_files:
        for path in export_files:
            with open(path, "r") as f:
                adapted = adapt(json.load(f))
            store.extend(adapted)
        logger.info(
            "Loaded {} export JSON file(s) -> {}".format(
                len(export_files), len(store._elements)
            )
        )
    elif sysml_files:
        # No exports yet: run the windtrader jar to produce per-file export JSON.
        jar = os.environ.get("WINDTRADER_JAR", "windtrader-java.jar")
        tmp = tempfile.mkdtemp(prefix="windstorm-export-")
        for path in sysml_files:
            name = os.path.basename(path)
            # batch-export reads file paths on stdin; run one at a time into tmp.
            with open(path, "rb") as infile:
                proc = subprocess.run(
                    ["java", "-jar", jar, "batch-export"],
                    input=path.encode(),
                    capture_output=True,
                    cwd=tmp,
                    timeout=300,
                )
            if proc.returncode != 0:
                logger.warning(
                    "batch-export failed for {}: {}".format(
                        name, proc.stderr.decode()[-300:]
                    )
                )
                continue
            out = os.path.join(tmp, name + ".export.json")
            if os.path.exists(out):
                with open(out, "r") as f:
                    store.extend(adapt(json.load(f)))
        if len(store._elements) == 0:
            raise RuntimeError(
                "No elements could be exported from .sysml in {}. "
                "Set WINDTRADER_JAR to the windtrader-java jar path.".format(source_dir)
            )
    else:
        raise RuntimeError(
            "No .export.json or .sysml files found in {}".format(source_dir)
        )

    logger.info("Local store built with {} element(s).".format(len(store._elements)))
    return store


def galestorm(
    element_name: str,
    api: str = "http://sysml2-dev.intercax.com:9000",
    source: str = "",
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
    """
    setup_logging(debug)

    api_store = None
    if source:
        # Offline mode: build an ElementStore from local files and run the
        # exact same templating core against it (no network).
        api_store = _load_local_store(source)
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
    fire.Fire(galestorm)


if __name__ == "__main__":
    main()
