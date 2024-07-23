import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

import filecmp
import shutil

import pytest
import responses

from windstorm.main import galestorm
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

    # Update the excel file using the long chain version, doesn't really matter
    galestorm(
        "case5",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    # Copy output file to hidden folder (to prevent other tests picking it up)
    shutil.copyfile(
        "./tests/mocks/1_analysis/output/template.xlsx",
        "./tests/mocks/1_analysis/xlsx_input/template_final.xlsx",
    )

    shutil.unpack_archive(
        "./tests/mocks/1_analysis/output/template.xlsx", "./srczip", "zip"
    )
    shutil.unpack_archive(
        "./tests/mocks/1_analysis/xlsx_input/output.xlsx", "./dstzip", "zip"
    )

    # Ensure that the file is the same bytewise as the expected output
    b = are_dir_trees_equal(
        "./srczip",
        "./dstzip",
    )

    shutil.rmtree("./srczip")
    shutil.rmtree("./dstzip")
    # Remove the template so that other tests don't pick up
    os.remove("./tests/mocks/1_analysis/input/template.xlsx")
    os.remove("./tests/mocks/1_analysis/output/template.xlsx")

    assert b


@responses.activate
def test_analysis_xlsx_force_skip():
    """This should skip the excel file since it can't be opened and push the
    file as is."""
    add_responses(project_response, "1_analysis")

    f1 = "./tests/mocks/1_analysis/input/binary.xlsx"
    f2 = f1.replace("input", "output")

    with open(f1, "wb") as f:
        ba = bytearray([123, 3, 255, 0, 100])
        f.write(ba)
    f.close()

    # Update the excel file using the long chain version, doesn't really matter
    galestorm(
        "case5",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    b = filecmp.cmp(f1, f2)
    os.remove(f1)
    os.remove(f2)

    assert b


@responses.activate
def test_analysis_xlsx_file_exists():
    """This should skip the excel file since it can't be opened and push the
    file as is."""
    add_responses(project_response, "1_analysis")

    f1 = "./tests/mocks/1_analysis/input/template.xlsx"
    f2 = f1.replace("input", "output")

    shutil.copyfile(
        "./tests/mocks/1_analysis/xlsx_input/template.xlsx",
        f1,
    )

    shutil.copyfile(f1, f2 + ".zip")

    # Update the excel file using the long chain version, doesn't really matter
    galestorm(
        "case5",
        api="http://sysml2.intercax.com:9000",
        in_directory="./tests/mocks/1_analysis/input",
        out_directory="./tests/mocks/1_analysis/output",
    )

    shutil.unpack_archive(
        "./tests/mocks/1_analysis/output/template.xlsx", "./srczip", "zip"
    )
    shutil.unpack_archive(
        "./tests/mocks/1_analysis/xlsx_input/output.xlsx", "./dstzip", "zip"
    )

    # Ensure that the file is the same bytewise as the expected output
    b = are_dir_trees_equal(
        "./srczip",
        "./dstzip",
    )

    shutil.rmtree("./srczip")
    shutil.rmtree("./dstzip")
    # Remove the template so that other tests don't pick up
    os.remove("./tests/mocks/1_analysis/input/template.xlsx")
    os.remove("./tests/mocks/1_analysis/output/template.xlsx")

    assert b
