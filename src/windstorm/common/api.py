import sys
import json
import uuid
import logging

logger = logging.getLogger("windstorm.common.api")

import requests

headers = {"Content-type": "application/json", "Accept": "text/plain"}

from windstorm.common.functions import github_issue_error, is_valid_uuid


def handle_request_response(r):
    if r.status_code == 404:
        logger.error("The project id could not be found.")
        sys.exit()
    if r.status_code != 200:
        # The address is reachable
        logger.error("API returned {} status code".format(r.status_code))
        github_issue_error()

    logger.debug("Response was correctly received.")

    try:
        response = r.json()
    except Exception as e:
        logger.error(e)
        github_issue_error()
    logger.debug("Response received in proper format.")

    if type(response) == type(list()):
        r2 = response
    else:
        r2 = [response]

    return r2


def check_for_api(api, project_id, verify=False):
    r = requests.get(api + "/projects?page%5Bsize%5D=1", verify=verify)
    if r.status_code == 200:
        logger.info("API Server found.")

    if project_id != "":
        r = requests.get(api + "/projects/" + project_id, verify=verify)
        # Grab a specific project
    response = handle_request_response(r)

    if len(response) == 1:
        return response[0]
    elif len(response) == 0:
        logger.error("Failed to find this project name.")
        sys.exit()
    else:
        logger.error(response)
        github_issue_error()


def validate(params):
    if not "value" in params:
        raise KeyError("No values set")
    if not "operator" in params:
        raise KeyError("No operators set")
    if not "property" in params:
        raise KeyError("No properties set")


def build_query(params):
    validate(params)
    base_query = {}
    base_query["@type"] = "Query"
    base_query["where"] = {}
    if len(params["value"]) == 1:
        base_query["where"]["@type"] = "PrimitiveConstraint"
        try:
            base_query["where"]["operator"] = params["operator"][0]
            base_query["where"]["property"] = params["property"][0]
            base_query["where"]["value"] = params["value"][0]
        except TypeError as e:
            logger.error("Input params were incorrect when passed to build a query")
            raise e
    elif len(params["value"]) > 1:
        base_query["where"]["@type"] = "CompositeConstraint"
        base_query["where"]["operator"] = "and"
        base_query["where"]["constraint"] = []
        for k, v in enumerate(params["value"]):
            constraint = {}
            constraint["@type"] = "PrimitiveConstraint"
            constraint["operator"] = params["operator"][k]
            constraint["property"] = params["property"][k]
            constraint["value"] = params["value"][k]
            base_query["where"]["constraint"].append(constraint)
    else:
        raise TypeError

    return json.dumps(base_query)


def query_for_element(api, project, base_query, verify=False):
    logger.debug(base_query)

    url = api + "/projects/" + project["@id"] + "/query-results"
    r = requests.post(url, data=base_query, headers=headers, verify=verify)
    response = handle_request_response(r)

    if len(response) == 1:
        return response[0]
    elif len(response) == 0:
        logger.error("Failed to find this element name.")
        sys.exit()


def get_element_by_id(api, project, eid, verify=False):
    q = build_query({"property": ["@id"], "operator": ["="], "value": [eid]})
    e = query_for_element(api, project, q, verify)
    return e


def get_element_by_name_type(api, project, element_name, element_type, verify=False):

    q = build_query(
        {
            "property": ["@type", "declaredName"],
            "operator": ["=", "="],
            "value": [element_type, element_name],
        }
    )

    eid = query_for_element(api, project, q, verify)
    return eid


def verify_tool(api, project_id, element_type, element_name, verify=False):
    # Grab the project from the API - either the latest or a specific one
    project = check_for_api(api, is_valid_uuid(project_id), verify)
    if "name" in project and "@id" in project:
        logger.info('Found project "{}" - {}'.format(project["name"], project["@id"]))
    else:
        logger.info("Response was {}.".format(project))
        raise KeyError

    # Check for analysis in the model
    eid = get_element_by_name_type(api, project, element_name, element_type)

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
            eid = get_element_by_id(api, project, a["@id"], verify)
        except KeyError:
            print("{}".format(sorted(list(a.keys()))))
            raise KeyError

        logger.info("Action: {}".format(eid["declaredName"]))

        # Check if this is a valid action with associated metadata
        if not "ownedElement" in eid:
            # This element doesn't own others
            logger.warning("Could not find ownedElement in action.")
            continue

        for oe in eid["ownedElement"]:
            oid = get_element_by_id(api, project, oe["@id"], verify)
            if "declaredName" in oid:
                logger.info("   Element: {}".format(oid["declaredName"]))
            else:
                logger.info("   Element Type: {}".format(oid["@type"]))

            if oid["@type"].lower() != "MetadataUsage".lower():
                # This owned element is not a MetaData
                logger.info("      Skipping non-metadata element.")
                continue

            # It's metadata
            logger.info("      Found metadata.")
            mdid = get_element_by_id(
                api, project, oid["metadataDefinition"]["@id"], verify
            )

            if mdid["qualifiedName"] != "AnalysisTooling::ToolExecution":
                continue

            logger.info("         Found analysis tool metadata.")

            for mdoe in oid["ownedElement"]:
                mdoeid = get_element_by_id(api, project, mdoe["@id"], verify)

                if mdoeid["@type"] != "ReferenceUsage" or mdoeid["name"] != "toolName":
                    continue

                if len(mdoeid["ownedElement"]) > 1:
                    raise NotImplementedError(
                        "Unhandled response: ReferenceUsage had more than one response"
                    )

                f = get_element_by_id(
                    api, project, mdoeid["ownedElement"][0]["@id"], verify
                )

                if f["value"] != "Windstorm":
                    continue

                logger.info("            Found windstorm tool metadata.")
                logger.info(
                    "            Adding action as valid windstorm analysis: {}".format(
                        eid["declaredName"]
                    )
                )
                aj.append(eid)

                if len(aj) > 0:
                    # Only find one time
                    break
            if len(aj) > 0:
                break
            ###### END LOOP for each element in owned element
    ###### END LOOP for each action
    return project, aj
