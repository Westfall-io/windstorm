import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src/windstorm"))

import filecmp
import shutil

import pytest
import responses

from windstorm import galestorm
from tests.common.functions import *

# Get the default project endpoint response.
project_response = project_response_fn()


@responses.activate
def test_analysis_xlsx_pass():
    """This should succeed and replace an excel file"""
    add_responses(project_response, "1_analysis")

    # Copy the template into the folder
    shutil.copyfile(
        "./tests/mocks/1_analysis/xlsx_input/template.xlsx",
        "./tests/mocks/1_analysis/input/template.xlsx",
    )

    shutil.copyfile(
        "./tests/mocks/1_analysis/input/template.xlsx",
        "./tests/mocks/1_analysis/xlsx_input/template_final.xlsx",
    )

    # Update the excel file using the long chain version, doesn't really matter
    galestorm(
        "case5",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    # Ensure that the file is the same bytewise as the expected output
    assert filecmp.cmp(
        "./tests/mocks/1_analysis/xlsx_input/output.xlsx",
        "./tests/mocks/1_analysis/output/template.xlsx",
    )

    # Remove the template so that other tests don't pick up
    os.remove("./tests/mocks/1_analysis/input/template.xlsx")
    os.remove("./tests/mocks/1_analysis/output/template.xlsx")
