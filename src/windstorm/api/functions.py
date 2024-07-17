import sys
import json
import logging

logger = logging.getLogger("windstorm.api")

import requests

headers = {"Content-type": "application/json", "Accept": "text/plain"}


def github_issue_error():
    logger.error("Unknown error. Please submit a issue on github.")
    raise NotImplementedError


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


def check_for_api(api, project_id):
    r = requests.get(api + "/projects?page%5Bsize%5D=1")
    if r.status_code == 200:
        logger.info("API Server found.")

    if project_id != "":
        r = requests.get(api + "/projects/" + project_id)
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


def query_for_element(api, project, base_query):
    logger.debug(base_query)

    url = api + "/projects/" + project["@id"] + "/query-results"
    r = requests.post(url, data=base_query, headers=headers)
    response = handle_request_response(r)

    if len(response) == 1:
        return response[0]
    elif len(response) == 0:
        logger.error("Failed to find this element name.")
        sys.exit()
