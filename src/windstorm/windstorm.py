import os
import sys
import logging

logger = logging.getLogger(__name__)
from pathlib import Path

import fire
from jinja2 import Template
from api.functions import check_for_api, query_for_element, build_query


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


def galestorm(
    project_id: str,
    element_name: str,
    api: str = "http://sysml2.intercax.com:9000",
    element_type: str = "AnalysisCaseDefinition",
    in_directory: str = ".",
    out_directory: str = ".",
    debug: bool = False,
):
    """
    This is a description of the program.

    """
    setup_logging(debug)

    # Grab the project from the API - either the latest or a specific one
    project = check_for_api(api, project_id)
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
                else:
                    # This owned element is not a MetaData
                    logger.info("      Skipping non-metadata element.")
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
                                q = build_query(
                                    {
                                        "property": ["@id"],
                                        "operator": ["="],
                                        "value": [valid["chainingFeature"][-1]["@id"]],
                                    }
                                )
                                chainid = query_for_element(api, project, q)
                                logger.debug(
                                    "         ChainElement: {}".format(chainid["@type"])
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
                                    else:
                                        pass
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
            else:
                logger.info("      Input had no metadata to associate to name.")
        ###### END LOOP for each input
        vars.append(thisvar)

    ###### END LOOP for action in metadata'd actions
    logger.debug(vars)

    output = {}
    for v in vars:
        output[v["name"]] = v["value"]

    logger.info(output)

    def windstorm(string):
        # This function is prep for using units
        return output[string]

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
                        template = Template(f.read())
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

                    # Overwrite anything in the current folder with the artifact
                    with open(outfile, "w") as f:
                        f.write(template.render(windstorm=windstorm, **output))


def main():
    fire.Fire(galestorm)


if __name__ == "__main__":
    main()
