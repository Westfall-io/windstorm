import os
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
    try:
        with open("./tests/mocks/1_analysis/input/template.txt", "r") as f:
            with open("./tests/mocks/1_analysis/output/template.txt", "w") as g:
                g.write(f.read())
    except:
        pass

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

    try:
        with open("./tests/mocks/1_analysis/input/template.txt", "r") as f:
            with open("./tests/mocks/1_analysis/output/template.txt", "w") as g:
                g.write(f.read())
    except:
        pass

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
    f.close()

    galestorm(
        "case3",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip() == "No"


@responses.activate
def test_analysis_success_debug():
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaT') }}")
    f.close()

    galestorm(
        "case3",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
        debug=True,
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip() == "No"


@responses.activate
def test_analysis_featurechain():
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaT') }}")
    f.close()

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
    f.close()

    galestorm(
        "case5",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip() == "1"


@responses.activate
def test_analysis_units():
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaT') }}")
    f.close()

    galestorm(
        "case6",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip() == "3"


@responses.activate
def test_failed_template():
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaE') }}")
    f.close()

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
    f.close()

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
    f.close()

    galestorm(
        "case3",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
        force_render_error_continue=True,
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read() == "{{ }"
    f.close()


@responses.activate
def test_analysis_success_binary_skip():
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaT') }}")
    f.close()

    with open("./tests/mocks/1_analysis/input/binary.b", "wb") as f:
        ba = bytearray([123, 3, 255, 0, 100])
        f.write(ba)
    f.close()

    galestorm(
        "case3",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    os.remove("./tests/mocks/1_analysis/input/binary.b")
    os.remove("./tests/mocks/1_analysis/output/binary.b")

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip() == "No"
    f.close()


@responses.activate
def test_analysis_novariables():
    """This should succeed and replace a file with 'No'"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaT') }}")
    f.close()

    with pytest.raises(SystemExit):
        galestorm(
            "case7",
            api="http://sysml2.intercax.com:9000",
            in_directory="./tests/mocks/1_analysis/input",
            out_directory="./tests/mocks/1_analysis/output",
        )


@responses.activate
def test_analysis_reference():
    """This should succeed and replace a file with 4"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaT') }}")
    f.close()

    galestorm(
        "case8",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip() == "4"
    f.close()


@responses.activate
def test_analysis_list():
    """This should succeed and replace a file with a list"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("{{ windstorm('deltaT') }}")
    f.close()

    galestorm(
        "case9",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
        debug=True,
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip().replace(" ", "") == "[1,2,3]"
    f.close()


@responses.activate
def test_analysis_jinjafor():
    """This should succeed and replace a file with a list"""
    add_responses(project_response, "1_analysis")

    with open("./tests/mocks/1_analysis/input/template.txt", "w") as f:
        f.write("Geopoint({% for k,v in enumerate(windstorm('deltaT')) %}")
        f.write("{% if k==len(windstorm('deltaT')) %}{{ v }}{% else %}{{ v }},")
        f.write("{% endfor %})")
    f.close()

    galestorm(
        "case9",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
        debug=True,
    )

    with open("./tests/mocks/1_analysis/output/template.txt", "r") as f:
        assert f.read().strip().replace(" ", "") == "[1,2,3]"
    f.close()
