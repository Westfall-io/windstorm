import json
import uuid as uuid_gen
from functools import partial
import filecmp
import os.path
import sys
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../src/windstorm"))

import responses
import requests

from windstorm import galestorm

# Both of these return the parent element
# r = requests.get(api + "/projects?page%5Bsize%5D=1")
# r = requests.get(api + "/projects/" + project_id)
# This will return the element
# url = api + "/projects/" + project["@id"] + "/query-results"


def are_dir_trees_equal(dir1, dir2):
    """
    Compare two directories recursively. Files in each directory are
    assumed to be equal if their names and contents are equal.

    @param dir1: First directory path
    @param dir2: Second directory path

    @return: True if the directory trees are the same and
        there were no errors while accessing the directories or files,
        False otherwise.
    """

    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if (
        len(dirs_cmp.left_only) > 0
        or len(dirs_cmp.right_only) > 0
        or len(dirs_cmp.funny_files) > 0
    ):
        return False
    (_, mismatch, errors) = filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False
    )
    if len(mismatch) > 0 or len(errors) > 0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not are_dir_trees_equal(new_dir1, new_dir2):
            return False
    return True


def request_callback(request_id, mock_dir):
    """
    This function handles reading json files to prepare the response like
    it's coming from the API.


    """
    payload = json.loads(request_id.body)
    # Sample Query
    # {
    # "@type": "Query",
    # "select": [
    # "@id"
    # ],
    # "where": {
    # "@type": "PrimitiveConstraint",
    # "operator": "=",
    # "property": "@type",
    # "value": "Element"
    # }
    # }
    # This doesn't handle all possible cases
    t1 = True
    if payload["@type"] == "Query":
        if payload["where"]["@type"] == "PrimitiveConstraint":
            if payload["where"]["property"] == "@id":
                eid = payload["where"]["value"]
            else:
                raise ValueError("The input query was not an @id")
        elif payload["where"]["@type"] == "CompositeConstraint":
            t1 = False
            if payload["where"]["operator"] == "and":
                for c in payload["where"]["constraint"]:
                    if c["property"] == "@type":
                        t = c["value"]
                    elif c["property"] == "declaredName":
                        dn = c["value"]
                    else:
                        raise ValueError("The input query was not handled")
            else:
                raise ValueError("The input query was not handled")
        else:
            raise ValueError("The input query was not a PrimitiveConstraint")
    else:
        raise ValueError("The input query was not a Query type")

    try:
        if t1:
            with open("./tests/mocks/" + mock_dir + "/" + eid + ".json", "r") as f:
                data = f.read()
        else:
            with open(
                "./tests/mocks/" + mock_dir + "/" + t + "_" + dn + ".json", "r"
            ) as f:
                data = f.read()
    except Exception as e:
        print(e)
        if t1:
            print("./tests/mocks/" + mock_dir + "/" + eid + ".json")
        else:
            print("./tests/mocks/" + mock_dir + "/" + t + "_" + dn + ".json")

        from os import walk

        for dirpath, dirnames, filenames in walk("./tests/mocks/" + mock_dir + "/"):
            print(filenames)
        raise NotImplementedError

    headers = {"Content-type": "application/json", "Accept": "text/plain"}
    return (200, headers, data)


with open("./tests/mocks/api_projects_response/projects.json", "r") as f:
    project_response = json.loads(f.read())


@responses.activate
def test_404_response():
    with pytest.raises(SystemExit):
        responses.add(
            responses.GET,
            "http://sysml2.intercax.com:9000/projects?page%5Bsize%5D=1",
            json={},
            status=404,
        )

        galestorm("case1", api="http://sysml2.intercax.com:9000")


@responses.activate
def test_500_response():
    with pytest.raises(NotImplementedError) as e_info:
        responses.add(
            responses.GET,
            "http://sysml2.intercax.com:9000/projects?page%5Bsize%5D=1",
            json={},
            status=500,
        )
        galestorm("case1", api="http://sysml2.intercax.com:9000")


@responses.activate
def test_wrong_type_response_response():
    responses.add(
        responses.GET,
        "http://sysml2.intercax.com:9000/projects?page%5Bsize%5D=1",
        json={},
        status=200,
    )

    galestorm("case1", api="http://sysml2.intercax.com:9000")


@responses.activate
def test_analysis_simple():
    responses.add(
        responses.GET,
        "http://sysml2.intercax.com:9000/projects?page%5Bsize%5D=1",
        json=project_response,
        status=200,
    )

    responses.add_callback(
        responses.POST,
        "http://sysml2.intercax.com:9000/projects/00270ef6-e518-455a-b59e-324ffeb1c9da/query-results",
        callback=partial(request_callback, mock_dir="1_analysis"),
        content_type="application/json",
    )

    analysis = ["case1", "case2"]
    for a in analysis:
        galestorm(
            a,
            api="http://sysml2.intercax.com:9000",
            in_directory="./tests/mocks/1_analysis/input",
            out_directory="./tests/mocks/1_analysis/output",
        )

        assert (
            are_dir_trees_equal(
                "./tests/mocks/1_analysis/input", "./tests/mocks/1_analysis/output"
            )
            == True
        )


## These are examples from responses. This one does a static response from a
## file.

# @responses.activate
# def test_1_analysis():
#    # Static response for projects
#    with open('./tests/mocks/api_projects_response/projects.json', 'r') as f:
#        project_response = f.read()
#
#    responses.add(
#        responses.GET,
#        "http://sysml2.intercax.com:9000/projects?page%5Bsize%5D=1",
#        json=project_response,
#        status=200,
#    )

# responses.add(
# responses.GET,
# re.compile("http://sysml2.intercax.com:9000/projects/([a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})"),
# json=project_response,
# status=200,
# )

#    assert resp.json() == {"error": "not found"}
#    assert resp.status_code == 404


# def return_json():
#    return {"error": "not found"}

## This one just uses a function to return a response.
# @responses.activate
# def test2_simple():
# Register via 'Response' object
#    rsp1 = responses.Response(
#        method="PUT",
#        url="http://example.com",
#    )
#    responses.add(rsp1)
#    # register via direct arguments
#    responses.add(
#        responses.GET,
#        "http://twitter.com/api/1/foobar",
#        json=return_json(),
#        status=404,
#    )

#    resp2 = requests.put("http://example.com")

#    assert resp2.status_code == 200
#    assert resp2.request.method == "PUT"
