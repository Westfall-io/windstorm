import os
import re
import sys
import logging

logger = logging.getLogger("windstorm.common.sysml")
import shutil

from pathlib import Path

from jinja2 import Template
from jinja2.exceptions import TemplateSyntaxError

from windstorm.common.api import get_element_by_id
from windstorm.common.functions import remove_file, rename_file, zip_file


def handle_literals(element):
    if element["@type"] == "LiteralInteger":
        logger.info("         Value: {}".format(element["value"]))
        v = element["value"]
    elif element["@type"] == "LiteralString":
        logger.info("         Value: {}".format(element["value"]))
        v = element["value"]
    elif element["@type"] == "LiteralRational":
        logger.info("         Value: {}".format(element["value"]))
        v = element["value"]
    elif element["@type"] == "LiteralBoolean":
        logger.info("         Value: {}".format(element["value"]))
        v = element["value"]
    else:
        return False, False

    return True, v


def check_append(v1, v2):
    # logger.info("         Append: {}, {}".format(v1, v2))
    if "value" in v2:
        if type(v2["value"]) == type(list()):
            v2["value"].append(v1)
        else:
            v2["value"] = v1
    else:
        v2["value"] = v1
    return v2


def handle_operator_expression(api, project, base_element, thisvar):
    for arg_id in base_element["argument"]:
        arg_element = get_element_by_id(api, project, arg_id["@id"])
        literal, value = handle_literals(arg_element)
        if literal:
            thisvar = check_append(value, thisvar)
        elif arg_element["@type"] == "OperatorExpression":
            if "value" in thisvar:
                thisvar["value"] = [thisvar["value"]]
            else:
                thisvar["value"] = []

            thisvar = handle_operator_expression(api, project, arg_element, thisvar)
        else:
            # logger.info(arg_element)
            logger.warning(
                "Could not find a valid type for this toolvariable, skipping."
            )
            logger.warning(
                "Please consider submitting this issue to github. The type was {}".format(
                    arg_element["@type"]
                )
            )

    return thisvar


def handle_feature_element(api, project, key, thisvar):
    v2 = get_element_by_id(api, project, key["@id"])
    logger.info("         Target Element: {}".format(v2["@type"]))

    literal, v = handle_literals(v2)
    if literal:
        # Skip the rest of this code if it's been handled.
        return check_append(v, thisvar)

    if v2["@type"] == "OperatorExpression":
        return handle_operator_expression(api, project, v2, thisvar)
        ###### END LOOP for each argument
    elif v2["@type"] == "Multiplicity":
        # Don't do anything for this right now.
        logger.info("Skipping found multiplicity.")
        pass
    elif v2["@type"] == "FeatureChainExpression":
        # This is a reference, do this over again
        v = handle_feature_chain(api, project, v2, thisvar)
        if type(v) != type(dict()):
            return check_append(v, thisvar)
        else:
            # This was probably a reference to a reference.
            return v
    else:
        logger.warning("Could not find a valid type for this toolvariable, skipping.")
        logger.warning(
            "Please consider submitting this issue to github. The type was {}".format(
                v2["@type"]
            )
        )
    ###### END IF @type
    return thisvar


def handle_feature_chain(api, project, voeid, thisvar):
    # logger.debug(voeid)
    valid = get_element_by_id(api, project, voeid["targetFeature"]["@id"])

    logger.debug("         TargetElement: {}".format(valid["@type"]))
    if "chainingFeature" in valid:

        if len(valid["chainingFeature"]) == 0:
            chainid = valid
        else:
            chainid = get_element_by_id(
                api, project, valid["chainingFeature"][-1]["@id"]
            )
            logger.debug("         ChainElement: {}".format(chainid["@type"]))

        if len(chainid["ownedElement"]) == 1:
            thisvar = handle_feature_element(
                api, project, chainid["ownedElement"][0], thisvar
            )
        else:
            for key in chainid["ownedElement"]:
                thisvar = handle_feature_element(api, project, key, thisvar)
                # Extra elements are probably multiplicity.
        ###### END LOOP if one element in attribute
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
        eid = get_element_by_id(api, project, a["@id"])
        logger.info("Action: {}".format(eid["declaredName"]))
        for var in eid["input"]:
            # Check each input
            varid = get_element_by_id(api, project, var["@id"])
            logger.info("   Input: {}".format(varid["declaredName"]))
            toolvarbool = False
            if "ownedElement" in varid:
                for voe in varid["ownedElement"]:
                    voeid = get_element_by_id(api, project, voe["@id"])

                    if voeid["@type"].lower() == "MetaDataUsage".lower():
                        mdid = get_element_by_id(
                            api, project, voeid["metadataDefinition"]["@id"]
                        )

                        if mdid["qualifiedName"] == "AnalysisTooling::ToolVariable":
                            toolvar = get_element_by_id(
                                api, project, voeid["ownedElement"][0]["@id"]
                            )
                            if toolvar["name"] == "name":
                                toolname = get_element_by_id(
                                    api, project, toolvar["ownedElement"][0]["@id"]
                                )
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
                        voeid = get_element_by_id(api, project, voe["@id"])
                        if voeid["@type"].lower() == "MetadataUsage".lower():
                            # Just skip it
                            continue

                        ename = voeid.get("declaredName", None)
                        if ename is None:
                            ename = voeid.get("@type", None)
                        logger.info("      Element: {}".format(ename))

                        literal, v = handle_literals(voeid)
                        if literal:
                            # Just go to the next element, it's been handled.
                            thisvar = check_append(v, thisvar)
                            continue

                        if voeid["@type"] == "FeatureChainExpression":
                            thisvar = handle_feature_chain(api, project, voeid, thisvar)
                            # logger.info("      {}".format(thisvar))
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
                try:
                    # Unpack the archive file
                    shutil.unpack_archive(thisfile, "./tmpzip", "zip")
                except shutil.ReadError:
                    if in_directory != out_directory:
                        with open(thisfile, "rb") as f1:
                            with open(outfile, "wb") as f2:
                                f2.write(f1.read())
                    logger.warning(
                        "Skipping excel file {}/{} because it could not be opened properly.".format(
                            dir_path, name
                        )
                    )
                    continue
                except PermissionError:
                    logger.error(
                        "Could not write files to template file: {}".format(thisfile)
                    )
                    sys.exit()

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
        zip_file(xlsx["filename"])

        # Ensure there isn't a file already there.
        remove_file(xlsx["filename"])

        # Remove the trailing .zip
        rename_file(xlsx["filename"] + ".zip", xlsx["filename"])

        # Remove the file if it still exists
        remove_file(xlsx["filename"] + ".zip")
    else:
        # Tell the user
        logger.info("Templating completed.")
