import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src/windstorm"))

from functools import partial

import pytest
import responses

from windstorm import galestorm
from common.functions import *

# Get the default project endpoint response.
project_response = project_response_fn()


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

    # Dynamic response for element search, project defined by json response

    responses.add_callback(
        responses.POST,
        "http://sysml2.intercax.com:9000/projects/00270ef6-e518-455a-b59e-324ffeb1c9da/query-results",
        callback=partial(request_callback, mock_dir='1_analysis'),
        content_type="application/json",
    )

    galestorm('case1',
        api = "http://sysml2.intercax.com:9000"
        in_directory = "./tests/mocks/1_analysis/input",
        out_directory = "./tests/mocks/1_analysis/output"
    )

    assert are_dir_trees_equal("./tests/mocks/1_analysis/input", "./tests/mocks/1_analysis/output") == True
