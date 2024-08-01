import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

import pytest

from windstorm.main import galestorm
from tests.common.functions import *

# Get the default project endpoint response.
project_response = project_response_fn()

def template(text):
    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write(text)
    f.close()

@responses.activate
def test_analysis_fail():
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    template("{{ windstorm('deltaT') }} {{ deltaE }}")

    galestorm(
        "case3",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip() == "No {{ deltaE }}"
