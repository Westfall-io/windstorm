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
    """Nothing to say this is a windstorm element"""

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
    """Nothing to say this is a windstorm element, but this one is inside
    of an action"""
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
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaT') }}")

    galestorm(
        "case3",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip() == "No"


@responses.activate
def test_analysis_featurechain():
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaT') }}")

    galestorm(
        "case4",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip() == "1.1"


@responses.activate
def test_analysis_featurechain_deeper():
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaT') }}")

    galestorm(
        "case5",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip() == "1"


@responses.activate
def test_failed_template():
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaE') }}")

    with pytest.raises(SystemExit):
        galestorm(
            "case3",
            api="http://sysml2.intercax.com:9000",
            in_directory="./tests/mocks/1_analysis/input",
            out_directory="./tests/mocks/1_analysis/output",
        )


@responses.activate
def test_failed_template_success():
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaE', 1) }}")

    galestorm(
        "case3",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip() == "1"


@responses.activate
def test_failed_template_forced_skip():
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ }")
    with open("./tests/mocks/1_analysis/input/template.txt", "r") as f:
        print(f.read())

    galestorm(
        "case3",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
        force_render_error_continue=True,
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read() == "{{ }\n"


@responses.activate
def test_analysis_success_binary_skip():
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaT') }}")

    with open("./tests/mocks/1_analysis/input/binary.b", "wb") as f:
        ba = bytearray([123, 3, 255, 0, 100])
        f.write(ba)

    galestorm(
        "case3",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip() == "No"
