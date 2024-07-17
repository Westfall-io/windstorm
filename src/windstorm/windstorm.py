import os
import sys
import uuid
import logging
import shutil

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


def handle_literals(element, variables):
    if element["@type"] == "LiteralInteger":
        logger.info("         Value: {}".format(element["value"]))
        variables["value"] = element["value"]
    elif element["@type"] == "LiteralString":
        logger.info("         Value: {}".format(element["value"]))
        variables["value"] = element["value"]
    elif element["@type"] == "LiteralRational":
        logger.info("         Value: {}".format(element["value"]))
        variables["value"] = element["value"]
    else:
        return False, variables

    return True, variables


def handle_feature_chain(api, project, voeid, thisvar):
    q = build_query(
        {
            "property": ["@id"],
            "operator": ["="],
            "value": [voeid["targetFeature"]["@id"]],
        }
    )
    valid = query_for_element(api, project, q)
    logger.debug("         TargetElement: {}".format(valid["@type"]))
    if "chainingFeature" in valid:

        if len(valid["chainingFeature"]) == 0:
            chainid = valid
        else:
            q = build_query(
                {
                    "property": ["@id"],
                    "operator": ["="],
                    "value": [valid["chainingFeature"][-1]["@id"]],
                }
            )
            chainid = query_for_element(api, project, q)
            logger.debug("         ChainElement: {}".format(chainid["@type"]))

        for key in chainid["ownedElement"]:
            q = build_query(
                {
                    "property": ["@id"],
                    "operator": ["="],
                    "value": [key["@id"]],
                }
            )
            v2 = query_for_element(api, project, q)

            literal, thisvar = handle_literals(v2, thisvar)
            if literal:
                # Skip the rest of this code if it's been handled.
                continue

            if v2["@type"] == "OperatorExpression":
                for arg in v2["argument"]:
                    q = build_query(
                        {
                            "property": ["@id"],
                            "operator": ["="],
                            "value": [arg["@id"]],
                        }
                    )
                    v3 = query_for_element(api, project, q)
                    literal, thisvar = handle_literals(v3, thisvar)

                    if not literal:
                        continue
                ###### END LOOP for each argument
            elif v2["@type"] == "Multiplicity":
                # Don't do anything for this right now.
                pass
            elif v2["@type"] == "FeatureChainExpression":
                # This is a reference, do this over again
                this_var = handle_feature_chain(api, project, v2, thisvar)
            else:
                logger.warning(
                    "Could not find a valid type for this toolvariable, skipping."
                )
                logger.warning(
                    "Please consider submitting this issue to github. The type was {}".format(
                        v2["@type"]
                    )
                )
            ###### END IF @type
        ###### END LOOP for each element in attribute
    else:
        # No chaining feature
        logger.error("No chaining feature found.")
        raise AttributeError

    return thisvar


def init_variables(api, project, aj):
    logger.info("---------------------------------")
    logger.info("Searching for input values.")
    logger.info("---------------------------------")
    # Now we have actions with windstorm tool execution metadata
    vars = []
    for a in aj:
        # Reset to base element
        q = build_query({"property": ["@id"], "operator": ["="], "value": [a["@id"]]})
        eid = query_for_element(api, project, q)
        logger.info("Action: {}".format(eid["declaredName"]))
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

                        literal, thisvar = handle_literals(voeid, thisvar)
                        if literal:
                            # Just go to the next element, it's been handled.
                            continue

                        if voeid["@type"] == "FeatureChainExpression":
                            thisvar = handle_feature_chain(api, project, voeid, thisvar)
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
    return output


def template_files(
    in_directory,
    out_directory,
    output,
    force_render_error_continue,
    xlsx={"unzip": False},
):
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
            # Make the filename
            thisfile = os.path.join(dir_path, name)
            # Path to the output file
            outfile = os.path.join(dir_path.replace(in_directory, out_directory), name)
            # Make a directory if it doesn't exist
            Path(dir_path.replace(in_directory, out_directory)).mkdir(
                parents=True, exist_ok=True
            )

            # If this file is an excel file, unzip it and template on the folder
            if ".xlsx" == thisfile[-5:] and not xlsx["unzip"]:

                logger.info(
                    "Found an excel spreadsheet. Attempting to reformat to be templated."
                )
                # Unpack the archive file
                shutil.unpack_archive(thisfile, "./tmpzip", "zip")

                # Run templates on all temporary files.
                template_files(
                    "./tmpzip",
                    "./tmpzip",
                    output,
                    force_render_error_continue,
                    xlsx={"unzip": True, "filename": outfile},
                )
                # Force it to look at the next file
                continue
            else:
                # Print this file to log
                logger.info(thisfile)

            if ".git" not in dir_path:
                try:
                    with open(thisfile, "r") as f:
                        # Skip the .git folder
                        data = f.read()
                    f.close()
                    template = Template(data, keep_trailing_newline=True)
                except UnicodeDecodeError:
                    with open(thisfile, "rb") as f:
                        # Skip the .git folder
                        data = f.read()
                    f.close()

                    if in_directory != out_directory:
                        with open(outfile, "wb") as f2:
                            f2.write(data)
                    logger.warning(
                        "Skipping file {}/{} because it was not text-based.".format(
                            dir_path, name
                        )
                    )
                    continue
                except TemplateSyntaxError as e:
                    with open(thisfile, "r") as f:
                        # Skip the .git folder
                        data = f.read()
                    f.close()

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
                    else:
                        pass

                    if in_directory != out_directory:
                        with open(outfile, "w") as f2:
                            f2.write(data)
                        f2.close()
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
                    f.write(
                        template.render(
                            windstorm=windstorm,
                            keep_trailing_newline=True,
                            **output,
                        )
                    )
                f.close()

    if xlsx["unzip"]:
        # Tell the user
        logger.info("Rezipping file to {}.".format(xlsx["filename"]))
        # Zip the file and overwrite
        shutil.make_archive(xlsx["filename"], "zip", "./tmpzip")
        # Remove the extra temporary folder
        shutil.rmtree("./tmpzip")
        # Remove the trailing .zip
        os.rename(xlsx["filename"] + ".zip", xlsx["filename"])
    else:
        # Tell the user
        logger.info("Templating completed.")


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
    if "name" in project and "@id" in project:
        logger.info('Found project "{}" - {}'.format(project["name"], project["@id"]))
    else:
        logger.info("Response was {}.".format(project))
        raise KeyError

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
        try:
            q = build_query(
                {"property": ["@id"], "operator": ["="], "value": [a["@id"]]}
            )
        except KeyError:
            print("{}".format(sorted(list(a.keys()))))
            raise KeyError
        eid = query_for_element(api, project, q)
        logger.info("Action: {}".format(eid["declaredName"]))

        # Check if this is a valid action with associated metadata
        if "ownedElement" in eid:
            for oe in eid["ownedElement"]:
                q = build_query(
                    {"property": ["@id"], "operator": ["="], "value": [oe["@id"]]}
                )
                oid = query_for_element(api, project, q)
                if "declaredName" in oid:
                    logger.info("   Element: {}".format(oid["declaredName"]))
                else:
                    logger.info("   Element Type: {}".format(oid["@type"]))

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
