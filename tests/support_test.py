import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src/windstorm"))

import pytest

from windstorm import galestorm

try:
    import windstorm.common.api as apif
except:
    import common.api as apif


def test_validate_query():
    with pytest.raises(KeyError):
        apif.validate({})

    with pytest.raises(KeyError):
        apif.validate({"value": "no"})

    with pytest.raises(KeyError):
        apif.validate({"value": "no", "operator": "no"})


def test_build_query():
    with pytest.raises(TypeError):
        apif.build_query({"value": 1, "operator": 1, "property": 1})


def test_build_query_2():
    with pytest.raises(TypeError):
        apif.build_query({"value": [1], "operator": 1, "property": 1})


def test_build_query_3():
    with pytest.raises(TypeError):
        apif.build_query({"value": [], "operator": 1, "property": 1})


def test_invalid_uuid():
    with pytest.raises(SystemExit):
        galestorm("case3", project_id="111")


if __name__ == "__main__":
    test_build_query()
