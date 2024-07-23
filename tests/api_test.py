import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

import pytest
import responses

from windstorm.main import galestorm
from tests.common.functions import *

# Get the default project endpoint response.
project_response = project_response_fn()


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
def test_wrong_type_response():
    with pytest.raises(KeyError) as e_info:
        responses.add(
            responses.GET,
            "http://sysml2.intercax.com:9000/projects?page%5Bsize%5D=1",
            json={},
            status=200,
        )

        galestorm("case1", api="http://sysml2.intercax.com:9000")


@responses.activate
def test_no_json_response():
    with pytest.raises(NotImplementedError) as e_info:
        responses.add(
            responses.GET,
            "http://sysml2.intercax.com:9000/projects?page%5Bsize%5D=1",
            body="",
            status=200,
        )

        galestorm("case1", api="http://sysml2.intercax.com:9000")


@responses.activate
def test_no_project_response():
    with pytest.raises(SystemExit) as e_info:
        responses.add(
            responses.GET,
            "http://sysml2.intercax.com:9000/projects?page%5Bsize%5D=1",
            json=project_response,
            status=200,
        )

        responses.add(
            responses.GET,
            "http://sysml2.intercax.com:9000/projects/00270ef6-e518-455a-b59e-324ffeb1c9da",
            json=[],
            status=200,
        )
        galestorm(
            "case1",
            api="http://sysml2.intercax.com:9000",
            project_id="00270ef6-e518-455a-b59e-324ffeb1c9da",
        )


@responses.activate
def test_bad_project_response():
    with pytest.raises(NotImplementedError) as e_info:
        responses.add(
            responses.GET,
            "http://sysml2.intercax.com:9000/projects?page%5Bsize%5D=1",
            json=project_response,
            status=200,
        )

        responses.add(
            responses.GET,
            "http://sysml2.intercax.com:9000/projects/00270ef6-e518-455a-b59e-324ffeb1c9da",
            json=[project_response, project_response],
            status=200,
        )
        galestorm(
            "case1",
            api="http://sysml2.intercax.com:9000",
            project_id="00270ef6-e518-455a-b59e-324ffeb1c9da",
        )


@responses.activate
def test_no_element_found():
    with pytest.raises(SystemExit) as e_info:
        responses.add(
            responses.GET,
            "http://sysml2.intercax.com:9000/projects?page%5Bsize%5D=1",
            json=project_response,
            status=200,
        )

        responses.add(
            responses.POST,
            "http://sysml2.intercax.com:9000/projects/00270ef6-e518-455a-b59e-324ffeb1c9da/query-results",
            json=[],
            status=200,
        )

        galestorm("case1", api="http://sysml2.intercax.com:9000")
