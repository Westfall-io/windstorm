import json
import logging

logger = logging.getLogger(__name__)

import requests


def api_error():
    import sys

    logger.error("Failed to connect to the API")
    sys.exit()


def handle_request_response(r, verify_first_element=True):
    if r.status_code != 200:
        # The address is reachable
        api_error()
    logger.debug("Server found.")

    try:
        response = r.json()
    except:
        # Response was not json
        api_error()
    logger.debug("Response received in proper format.")

    if verify_first_element:
        if type(response) == type(list()):
            # Convert to a dictionary
            r2 = response[0]
            logger.debug("Converting to dictionary")
        else:
            r2 = response
            logger.debug("Response not a list.")

        if type(r2) != type(dict()):
            # Make sure this is a proper response now
            print(type(r2), r2, response)
            api_error()
        logger.debug("Response was a dictionary.")

        return r2
    else:
        return response


def check_for_api(api, project_id):
    if project_id == "":
        r = requests.get(api + "/projects?page%5Bsize%5D=1")
        # This will always get the most recent project, at least, I hope
    else:
        r = requests.get(api + "/projects/" + project_id)
        # Grab a specific project
    response = handle_request_response(r)
    return response


def validate(params):
    if not "value" in params:
        raise AttributeError("No values set")
    if not "operator" in params:
        raise AttributeError("No operators set")
    if not "property" in params:
        raise AttributeError("No properties set")


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
        except Exception as e:
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

    return json.dumps(base_query)


def query_for_element(api, project, base_query):
    logger.debug(base_query)

    url = api + "/projects/" + project["@id"] + "/query-results"
    headers = {"Content-type": "application/json", "Accept": "text/plain"}
    r = requests.post(url, data=base_query, headers=headers)
    response = handle_request_response(r, False)
    return response[0]
