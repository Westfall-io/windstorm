import logging

logger = logging.getLogger("windstorm")

import fire

from windstorm.common.functions import setup_logging
from windstorm.common.api import verify_tool
from windstorm.common.sysml import init_variables, template_files


def galestorm(
    element_name: str,
    api: str = "http://sysml2-dev.intercax.com:9000",
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

    """
    setup_logging(debug)

    project, aj = verify_tool(api, project_id, element_type, element_name, insecure)

    if len(aj) == 0:
        if in_directory == out_directory:
            logger.info("Nothing to do, closing...")
        else:
            logger.info("Copying all files from input to output, no changes...")
            from distutils.dir_util import copy_tree

            copy_tree(in_directory, out_directory)
    else:
        output = init_variables(api, project, aj)
        template_files(in_directory, out_directory, output, force_render_error_continue)


def main():
    fire.Fire(galestorm)


if __name__ == "__main__":
    main()
