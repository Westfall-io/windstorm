import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

import shutil

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
def test_analysis_skip_extra_value():
    """This should succeed and replace a portion of the file with 'No'"""
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


@responses.activate
def test_analysis_helm_test():
    """This should not throw any errors, there's nothing to replace"""
    add_responses(project_response, "1_analysis")

    galestorm(
        "case3",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/minio/",
        out_directory="./tests/minio_o",
    )

    assert are_dir_trees_equal("./tests/minio/", "./tests/minio_o") == True

@responses.activate
def test_analysis_helm_test():
    """This should not throw any errors, there's nothing to replace"""
    add_responses(project_response, "1_analysis")

    f = open('./tests/minio/templates/configmap.yaml', 'r')
    g = open('./tests/minio/templates/configmap2.yaml', 'w')
    d = f.read()
    g.write('{{ windstorm("deltaT") }}'+d)
    f.close()
    g.close()

    galestorm(
        "case3",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/minio/",
        out_directory="./tests/minio_o",
    )

    f = open('./tests/minio/templates/configmap.yaml', 'r')
    g = open('./tests/minio_o/templates/configmap2.yaml', 'r')
    a = f.read()
    b = g.read()
    f.close()
    g.close()
    shutil.rmtree("./tests/minio_o")
    os.remove("./tests/minio/templates/configmap2.yaml")
    assert "No" + a == b
