import os
import sys
import uuid
import logging

logger = logging.getLogger(__name__)
from pathlib import Path

import fire
from jinja2 import Template
from jinja2.exceptions import TemplateSyntaxError

try:
    # Installed from PyPI
    from windstorm.api.functions import check_for_api, query_for_element, build_query
except ModuleNotFoundError:
    try:
        # Local Dev
        from api.functions import check_for_api, query_for_element, build_query
    except ModuleNotFoundError as e:
        logger.error("Module import error. Please submit a issue on github.")
        raise e


def setup_logging(debug):
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]

    for logger in loggers:
        if debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        logger.addHandler(handler)
        logger.propagate = False


def is_valid_uuid(val):
    if val == "":
        return val
    else:
        try:
            uuid.UUID(str(val))
            return val
        except ValueError:
            logger.error("The project id was not passed as a valid uuid.")
            sys.exit()


def galestorm(
    element_name: str,
    api: str = "http://sysml2.intercax.com:9000",
    project_id: str = "",
    element_type: str = "AnalysisCaseDefinition",
    in_directory: str = ".",
    out_directory: str = ".",
    force_render_error_continue: bool = False,
    debug: bool = False,
):
    """
    This is a description of the program.

    """
    setup_logging(debug)

    # Grab the project from the API - either the latest or a specific one
    project = check_for_api(api, is_valid_uuid(project_id))
    logger.info('Found project "{}" - {}'.format(project["name"], project["@id"]))

    # Check for analysis in the model
    q = build_query(
        {
            "property": ["@type", "declaredName"],
            "operator": ["=", "="],
            "value": [element_type, element_name],
        }
    )

    eid = query_for_element(api, project, q)

    if "ownedAction" in eid:
        actions = []
        for oa in eid["ownedAction"]:
            actions.append(oa)

    logger.info("Found {} actions.".format(len(actions)))

    if len(actions) == 0:
        # No actions, so the analysis definition is the main element
        actions = [eid]

    aj = []
    for a in actions:
        q = build_query({"property": ["@id"], "operator": ["="], "value": [a["@id"]]})
        eid = query_for_element(api, project, q)
        logger.info("Action: {}".format(eid["declaredName"]))

        # Check if this is a valid action with associated metadata
        if "ownedElement" in eid:
            for oe in eid["ownedElement"]:
                q = build_query(
                    {"property": ["@id"], "operator": ["="], "value": [oe["@id"]]}
                )
                oid = query_for_element(api, project, q)
                logger.info("   Element: {}".format(oid["declaredName"]))

                if oid["@type"].lower() == "MetadataUsage".lower():
                    logger.info("      Found metadata.")
                    q = build_query(
                        {
                            "property": ["@id"],
                            "operator": ["="],
                            "value": [oid["metadataDefinition"]["@id"]],
                        }
                    )
                    mdid = query_for_element(api, project, q)

                    if mdid["qualifiedName"] == "AnalysisTooling::ToolExecution":
                        logger.info("         Found analysis tool metadata.")

                        for mdoe in oid["ownedElement"]:
                            q = build_query(
                                {
                                    "property": ["@id"],
                                    "operator": ["="],
                                    "value": [mdoe["@id"]],
                                }
                            )
                            mdoeid = query_for_element(api, project, q)

                            if (
                                mdoeid["@type"] == "ReferenceUsage"
                                and mdoeid["name"] == "toolName"
                            ):
                                if len(mdoeid["ownedElement"]) > 1:
                                    raise NotImplementedError(
                                        "Unhandled "
                                        + "response: ReferenceUsage had more "
                                        + "than one response"
                                    )
                                else:
                                    q = build_query(
                                        {
                                            "property": ["@id"],
                                            "operator": ["="],
                                            "value": [mdoeid["ownedElement"][0]["@id"]],
                                        }
                                    )
                                    f = query_for_element(api, project, q)
                                    if f["value"] == "Windstorm":
                                        logger.info(
                                            "            Found windstorm tool metadata."
                                        )
                                        logger.info(
                                            "            Adding action as valid windstorm analysis: {}".format(
                                                eid["declaredName"]
                                            )
                                        )
                                        aj.append(eid)
                            if len(aj) > 0:
                                break
                else:
                    # This owned element is not a MetaData
                    logger.info("      Skipping non-metadata element.")

                if len(aj) > 0:
                    break
            ###### END LOOP for each element in owned element
        else:
            # This element doesn't own others
            logger.warning("Could not find ownedElement in action.")
    ###### END LOOP for each action

    logger.info("---------------------------------")
    logger.info("Searching for input values.")
    logger.info("---------------------------------")
    # Now we have actions with windstorm tool execution metadata
    for a in aj:
        # Reset to base element
        q = build_query({"property": ["@id"], "operator": ["="], "value": [a["@id"]]})
        eid = query_for_element(api, project, q)
        logger.info("Action: {}".format(eid["declaredName"]))
        vars = []
        for var in eid["input"]:
            # Check each input
            q = build_query(
                {"property": ["@id"], "operator": ["="], "value": [var["@id"]]}
            )
            varid = query_for_element(api, project, q)
            logger.info("   Input: {}".format(varid["declaredName"]))
            toolvarbool = False
            if "ownedElement" in varid:
                for voe in varid["ownedElement"]:
                    q = build_query(
                        {"property": ["@id"], "operator": ["="], "value": [voe["@id"]]}
                    )
                    voeid = query_for_element(api, project, q)

                    if voeid["@type"].lower() == "MetaDataUsage".lower():
                        q = build_query(
                            {
                                "property": ["@id"],
                                "operator": ["="],
                                "value": [voeid["metadataDefinition"]["@id"]],
                            }
                        )
                        mdid = query_for_element(api, project, q)

                        if mdid["qualifiedName"] == "AnalysisTooling::ToolVariable":
                            q = build_query(
                                {
                                    "property": ["@id"],
                                    "operator": ["="],
                                    "value": [voeid["ownedElement"][0]["@id"]],
                                }
                            )
                            toolvar = query_for_element(api, project, q)
                            if toolvar["name"] == "name":
                                q = build_query(
                                    {
                                        "property": ["@id"],
                                        "operator": ["="],
                                        "value": [toolvar["ownedElement"][0]["@id"]],
                                    }
                                )
                                toolname = query_for_element(api, project, q)
                                logger.info(
                                    "      Tool Variable: {}".format(toolname["value"])
                                )
                                toolvarbool = True
                                thisvar = {"name": toolname["value"]}
            else:
                logger.warning("No owned elements in this variable.")

            logger.info("      ---------------------------------")
            logger.info(
                "      Finding actual input values to link to tool variable names."
            )
            logger.info("      ---------------------------------")
            if toolvarbool:
                if "ownedElement" in varid:
                    for voe in varid["ownedElement"]:
                        # Look for a feature chain expression
                        q = build_query(
                            {
                                "property": ["@id"],
                                "operator": ["="],
                                "value": [voe["@id"]],
                            }
                        )
                        voeid = query_for_element(api, project, q)
                        if voeid["@type"].lower() == "MetadataUsage".lower():
                            # Just skip it
                            continue

                        ename = voeid.get("declaredName", None)
                        if ename is None:
                            ename = voeid.get("@type", None)
                        logger.info("      Element: {}".format(ename))
                        if voeid["@type"] == "FeatureChainExpression":
                            q = build_query(
                                {
                                    "property": ["@id"],
                                    "operator": ["="],
                                    "value": [voeid["targetFeature"]["@id"]],
                                }
                            )
                            valid = query_for_element(api, project, q)
                            logger.debug(
                                "         TargetElement: {}".format(valid["@type"])
                            )
                            if "chainingFeature" in valid:

                                if len(valid["chainingFeature"]) == 0:
                                    chainid = valid
                                else:
                                    q = build_query(
                                        {
                                            "property": ["@id"],
                                            "operator": ["="],
                                            "value": [
                                                valid["chainingFeature"][-1]["@id"]
                                            ],
                                        }
                                    )
                                    chainid = query_for_element(api, project, q)
                                    logger.debug(
                                        "         ChainElement: {}".format(
                                            chainid["@type"]
                                        )
                                    )

                                for key in chainid["ownedElement"]:
                                    q = build_query(
                                        {
                                            "property": ["@id"],
                                            "operator": ["="],
                                            "value": [key["@id"]],
                                        }
                                    )
                                    v2 = query_for_element(api, project, q)
                                    if v2["@type"] == "LiteralInteger":
                                        logger.info(
                                            "         Value: {}".format(v2["value"])
                                        )
                                        thisvar["value"] = v2["value"]
                                    elif v2["@type"] == "LiteralString":
                                        logger.info(
                                            "         Value: {}".format(v2["value"])
                                        )
                                        thisvar["value"] = v2["value"]
                                    elif v2["@type"] == "OperatorExpression":
                                        for arg in v2["argument"]:
                                            q = build_query(
                                                {
                                                    "property": ["@id"],
                                                    "operator": ["="],
                                                    "value": [arg["@id"]],
                                                }
                                            )
                                            v3 = query_for_element(api, project, q)

                                            if v3["@type"] == "LiteralInteger":
                                                logger.info(
                                                    "         Value: {}".format(
                                                        v3["value"]
                                                    )
                                                )
                                                thisvar["value"] = v3["value"]
                                            elif v3["@type"] == "LiteralString":
                                                logger.info(
                                                    "         Value: {}".format(
                                                        v3["value"]
                                                    )
                                                )
                                                thisvar["value"] = v3["value"]
                                            else:
                                                continue
                                        ###### END LOOP for each argument
                                    elif v2["@type"] == "Multiplicity":
                                        # Don't do anything for this right now.
                                        pass
                                    else:
                                        logger.warning(
                                            "Could not find a valid type for this toolvariable, skipping."
                                        )
                                        logger.warning(
                                            "Please consider submitting this issue to github. The type was {}".format(
                                                v2["@type"]
                                            )
                                        )
                                ###### END LOOP for each element in attribute
                            else:
                                # No chaining feature
                                logger.error("No chaining feature found.")
                                raise AttributeError
                        else:
                            # No chaining feature
                            logger.debug(
                                "         Skipping over element: {}".format(
                                    voeid["@type"]
                                )
                            )
                    ###### END LOOP for each element in owned element
                else:
                    # No chaining feature
                    logger.error("No ownedElement found.")
                    raise AttributeError

                vars.append(thisvar)
            else:
                logger.info("      Input had no metadata to associate to name.")

        ###### END LOOP for each input

    ###### END LOOP for action in metadata'd actions
    if len(aj) > 0:
        logger.debug(vars)

    output = {}
    for v in vars:
        if "value" in v:
            output[v["name"]] = v["value"]
        else:
            logger.warn(
                "Key: {} had no value associated to it, it might not be parsable.".format(
                    v["name"]
                )
            )

    logger.info(output)

    def windstorm(string, default=None):
        if string in output:
            return output[string]
        elif default is not None:
            return default
        else:
            logger.error(
                "Key: {} was not found in the model and no default value was given for template.".format(
                    string
                )
            )
            sys.exit()

    logger.info("Replacing variables in files with values.")
    for dir_path, dir_names, file_names in os.walk(in_directory):
        for name in file_names:
            thisfile = os.path.join(dir_path, name)
            logger.info(thisfile)
            outfile = os.path.join(dir_path.replace(in_directory, out_directory), name)
            Path(dir_path.replace(in_directory, out_directory)).mkdir(
                parents=True, exist_ok=True
            )
            if ".git" not in dir_path:
                with open(thisfile, "r") as f:
                    # Skip the .git folder
                    try:
                        template = Template(f.read(), keep_trailing_newline=True)
                    except UnicodeDecodeError:
                        if in_directory != out_directory:
                            with open(outfile, "w") as f2:
                                f2.write(f.read())
                        logger.warning(
                            "Skipping file {}/{} because it was not text-based.".format(
                                dir_path, name
                            )
                        )
                        continue
                    except TemplateSyntaxError as e:
                        if not force_render_error_continue:
                            user = input(
                                "The file {}/{} has template errors, do you wish to proceed?\n[y/n] ".format(
                                    dir_path, name
                                )
                            )
                            while user != "y":
                                if user == "n":
                                    sys.exit()
                                logger.warning("Please enter [y/n] to continue.")
                                user = input(
                                    "The file {}/{} has template errors, do you wish to proceed?\n[y/n] ".format(
                                        dir_path, name
                                    )
                                )

                        if in_directory != out_directory:
                            with open(outfile, "w") as f2:
                                f2.write(f.read())
                        logger.warning(
                            "Skipping file {}/{} because it had a template error.".format(
                                dir_path, name
                            )
                        )
                        logger.warning(
                            "   The template error was reported as: {}".format(e)
                        )
                        continue

                    # Overwrite anything in the current folder with the artifact
                    with open(outfile, "w") as f:
                        f.write(template.render(windstorm=windstorm, **output))


def main():
    fire.Fire(galestorm)


if __name__ == "__main__":
    main()
