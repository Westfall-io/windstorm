import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

import pytest
import responses

from windstorm.main import windstorm
from windstorm.common.errors import WindstormLookupError
from tests.common.functions import *

# Get the default project endpoint response.
project_response = project_response_fn()

defaultUrl = "http://sysml2-dev.intercax.com:9000"


@responses.activate
def test_404_response():
    # #96: library (windstorm()) raises WindstormLookupError; CLI (main())
    # converts to exit. Not SystemExit from the library path.
    with pytest.raises(WindstormLookupError):
        responses.add(
            responses.GET,
            defaultUrl + "/projects?page%5Bsize%5D=1",
            json={},
            status=404,
        )

        windstorm("case1", api=defaultUrl)


@responses.activate
def test_500_response():
    with pytest.raises(NotImplementedError) as e_info:
        responses.add(
            responses.GET,
            defaultUrl + "/projects?page%5Bsize%5D=1",
            json={},
            status=500,
        )
        windstorm("case1", api=defaultUrl)


@responses.activate
def test_wrong_type_response():
    # #96: a project response without name/@id is a lookup failure. windstorm()
    # (the library entrypoint) raises WindstormLookupError so a programmatic
    # caller can trap it; the CLI boundary (main()) converts it to exit 1.
    with pytest.raises(WindstormLookupError):
        responses.add(
            responses.GET,
            defaultUrl + "/projects?page%5Bsize%5D=1",
            json={},
            status=200,
        )

        windstorm("case1", api=defaultUrl)


@responses.activate
def test_no_json_response():
    with pytest.raises(NotImplementedError) as e_info:
        responses.add(
            responses.GET,
            defaultUrl + "/projects?page%5Bsize%5D=1",
            body="",
            status=200,
        )

        windstorm("case1", api=defaultUrl)


@responses.activate
def test_no_project_response():
    with pytest.raises(WindstormLookupError):
        responses.add(
            responses.GET,
            defaultUrl + "/projects?page%5Bsize%5D=1",
            json=project_response,
            status=200,
        )

        responses.add(
            responses.GET,
            defaultUrl + "/projects/00270ef6-e518-455a-b59e-324ffeb1c9da",
            json=[],
            status=200,
        )
        windstorm(
            "case1",
            api=defaultUrl,
            project_id="00270ef6-e518-455a-b59e-324ffeb1c9da",
        )


@responses.activate
def test_bad_project_response():
    with pytest.raises(NotImplementedError) as e_info:
        responses.add(
            responses.GET,
            defaultUrl + "/projects?page%5Bsize%5D=1",
            json=project_response,
            status=200,
        )

        responses.add(
            responses.GET,
            defaultUrl + "/projects/00270ef6-e518-455a-b59e-324ffeb1c9da",
            json=[project_response, project_response],
            status=200,
        )
        windstorm(
            "case1",
            api=defaultUrl,
            project_id="00270ef6-e518-455a-b59e-324ffeb1c9da",
        )


@responses.activate
def test_no_element_found():
    # #96: no element found in API query is a WindstormLookupError (not sys.exit).
    with pytest.raises(WindstormLookupError):
        responses.add(
            responses.GET,
            defaultUrl + "/projects?page%5Bsize%5D=1",
            json=project_response,
            status=200,
        )

        responses.add(
            responses.POST,
            defaultUrl + "/projects/00270ef6-e518-455a-b59e-324ffeb1c9da/query-results",
            json=[],
            status=200,
        )

        windstorm("case1", api=defaultUrl)
