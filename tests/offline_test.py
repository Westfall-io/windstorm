import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

import pytest
import responses

from windstorm.main import galestorm


def test_offline_source_renders_without_api(tmp_path):
    """--source renders entirely offline: no HTTP, values from local export JSON."""
    # A template referencing a ToolVariable input.
    (tmp_path / "input").mkdir()
    (tmp_path / "output").mkdir()
    (tmp_path / "input" / "template.txt").write_text('{{ windstorm("deltaT") }}')

    # Any network access would raise immediately -> proves offline path.
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add_passthru("http://placeholder.invalid")  # ensure nothing matches

        galestorm(
            "case3",
            source=os.path.join(
                os.path.dirname(__file__), "mocks", "1_analysis"
            ),
            in_directory=str(tmp_path / "input"),
            out_directory=str(tmp_path / "output"),
        )

    out = tmp_path / "output" / "template.txt"
    assert out.exists()
    assert out.read_text().strip() == "No"
