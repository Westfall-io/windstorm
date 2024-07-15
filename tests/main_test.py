import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src/windstorm"))

import pytest
import responses

from windstorm import galestorm
from tests.common.functions import *

# Get the default project endpoint response.
project_response = project_response_fn()


@responses.activate
def test_analysis_no_meta_no_action():
    """ Nothing to say this is a windstorm element """

    add_responses(project_response, "1_analysis")

        galestorm(
            "case1",
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

@responses.activate
def test_analysis_no_meta():
    """ Nothing to say this is a windstorm element, but this one is inside
    of an action """
    add_responses(project_response, "1_analysis")

        galestorm(
            "case2",
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

@responses.activate
def test_analysis_success():
    """ This should succeed and replace a file with 'No' """
    add_responses(project_response, "1_analysis")

        galestorm(
            "case3",
            api="http://sysml2.intercax.com:9000",
            in_directory="./tests/mocks/1_analysis/input",
            out_directory="./tests/mocks/1_analysis/output",
        )
        with open("./tests/mocks/1_analysis/output/template.txt", 'r') as f:
            assert f.read() == 'No'


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
