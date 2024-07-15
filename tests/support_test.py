import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src/windstorm"))

import pytest

import api.functions as apif


def test_validate_query():
    with pytest.raises(KeyError):
        apif.validate({})

    with pytest.raises(KeyError):
        apif.validate({"value": "no"})

    with pytest.raises(KeyError):
        apif.validate({"value": "no", "operator": "no"})


def test_build_query():
    with pytest.raises(TypeError):
        apif.validate({"value": 1, "operator": 1, "property": 1})
