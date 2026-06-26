"""Tests for getClusterParameter accepted argument forms.

Covers the accepted argument forms: single string, wildcard, array of
strings, duplicate names, and the extra comment field.

Categories: #2, #10
"""

import pytest

from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq, Len

pytestmark = pytest.mark.admin

_VALID_PARAM = "changeStreamOptions"
_VALID_PARAM_2 = "changeStreams"


def test_getClusterParameter_wildcard_returns_all(collection):
    """Test '*' argument returns all available cluster parameters with ok:1."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Wildcard '*' should return ok:1")


def test_getClusterParameter_single_name_returns_one(collection):
    """Test single string name returns exactly one clusterParameters entry."""
    result = execute_admin_command(collection, {"getClusterParameter": _VALID_PARAM})
    assertProperties(
        result,
        {"ok": Eq(1.0), "clusterParameters": Len(1)},
        msg="Single name should return ok:1 with one parameter",
        raw_res=True,
    )


def test_getClusterParameter_array_two_names_returns_two(collection):
    """Test array of two valid names returns two clusterParameters entries."""
    result = execute_admin_command(
        collection, {"getClusterParameter": [_VALID_PARAM, _VALID_PARAM_2]}
    )
    assertProperties(
        result,
        {"ok": Eq(1.0), "clusterParameters": Len(2)},
        msg="Array of two names should return two parameters",
        raw_res=True,
    )


def test_getClusterParameter_array_duplicate_names(collection):
    """Test array with duplicate valid names succeeds."""
    result = execute_admin_command(
        collection, {"getClusterParameter": [_VALID_PARAM, _VALID_PARAM]}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Duplicate names in array should succeed")


def test_getClusterParameter_unrecognized_field_accepted(collection):
    """Test extra comment field is accepted (MongoDB treats it as generic command field)."""
    result = execute_admin_command(collection, {"getClusterParameter": "*", "comment": "test"})
    assertSuccessPartial(result, {"ok": 1.0}, msg="comment field should be accepted")
