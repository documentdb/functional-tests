"""Tests for getClusterParameter argument handling.

Covers BSON type rejection/acceptance for the <parameter> argument,
argument forms (single/array/wildcard/empty), undocumented coercion
edge cases, array-form edge cases, and command-document quirks.

Categories: #1, #2, #3 (type/field portions), #6, #10, #15
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    COMMAND_NOT_FOUND_ERROR,
    NO_SUCH_KEY_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin

_VALID_PARAM = "changeStreamOptions"
_VALID_PARAM_2 = "changeStreams"


# ---------------------------------------------------------------------------
# §1 / §6  BSON type rejection for non-string / non-array argument types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TypeCase(BaseTestCase):
    """Test case for <parameter> type handling."""

    arg: Any = None


_REJECT_TYPES: list[TypeCase] = [
    TypeCase("int", arg=1, error_code=TYPE_MISMATCH_ERROR, msg="Should reject int"),
    TypeCase("int64", arg=Int64(1), error_code=TYPE_MISMATCH_ERROR, msg="Should reject Int64"),
    TypeCase("double", arg=3.14, error_code=TYPE_MISMATCH_ERROR, msg="Should reject double"),
    TypeCase(
        "decimal128",
        arg=Decimal128("1"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject Decimal128",
    ),
    TypeCase("bool_true", arg=True, error_code=TYPE_MISMATCH_ERROR, msg="Should reject bool true"),
    TypeCase(
        "bool_false", arg=False, error_code=TYPE_MISMATCH_ERROR, msg="Should reject bool false"
    ),
    TypeCase("object", arg={"a": 1}, error_code=TYPE_MISMATCH_ERROR, msg="Should reject object"),
    TypeCase(
        "bindata",
        arg=Binary(b"x"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject binData",
    ),
    TypeCase(
        "objectid",
        arg=ObjectId("000000000000000000000000"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject ObjectId",
    ),
    TypeCase(
        "date",
        arg=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject date",
    ),
    TypeCase("regex", arg=Regex("x"), error_code=TYPE_MISMATCH_ERROR, msg="Should reject regex"),
    TypeCase(
        "javascript",
        arg=Code("function(){}"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject JavaScript",
    ),
    TypeCase(
        "timestamp",
        arg=Timestamp(0, 1),
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject Timestamp",
    ),
    TypeCase("minkey", arg=MinKey(), error_code=TYPE_MISMATCH_ERROR, msg="Should reject MinKey"),
    TypeCase("maxkey", arg=MaxKey(), error_code=TYPE_MISMATCH_ERROR, msg="Should reject MaxKey"),
    TypeCase("null", arg=None, error_code=TYPE_MISMATCH_ERROR, msg="Should reject null"),
]


@pytest.mark.parametrize("test", pytest_params(_REJECT_TYPES))
def test_getClusterParameter_rejects_invalid_bson_type(collection, test):
    """Test getClusterParameter rejects non-string/non-array argument types."""
    result = execute_admin_command(collection, {"getClusterParameter": test.arg})
    assertFailureCode(result, test.error_code, msg=test.msg)


# ---------------------------------------------------------------------------
# §2  Argument forms — accepted
# ---------------------------------------------------------------------------


def test_getClusterParameter_wildcard_returns_all(collection):
    """Test '*' argument returns all available cluster parameters with ok:1."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Wildcard '*' should return ok:1")


def test_getClusterParameter_single_name_returns_one(collection):
    """Test single string name returns exactly one clusterParameters entry."""
    result = execute_admin_command(collection, {"getClusterParameter": _VALID_PARAM})
    from documentdb_tests.framework.assertions import assertProperties
    from documentdb_tests.framework.property_checks import Eq, Len

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
    from documentdb_tests.framework.assertions import assertProperties
    from documentdb_tests.framework.property_checks import Eq, Len

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


# ---------------------------------------------------------------------------
# §2  Argument forms — rejected
# ---------------------------------------------------------------------------


def test_getClusterParameter_empty_array_errors(collection):
    """Test empty array argument fails with BAD_VALUE_ERROR."""
    result = execute_admin_command(collection, {"getClusterParameter": []})
    assertFailureCode(result, BAD_VALUE_ERROR, msg="Empty array must supply at least one name")


def test_getClusterParameter_array_nonstring_element_rejects(collection):
    """Test array containing a non-string element fails with TYPE_MISMATCH_ERROR."""
    result = execute_admin_command(collection, {"getClusterParameter": [_VALID_PARAM, 123]})
    assertFailureCode(
        result, TYPE_MISMATCH_ERROR, msg="Non-string array element should be rejected"
    )


def test_getClusterParameter_unknown_name_errors(collection):
    """Test an unknown parameter name fails with NO_SUCH_KEY_ERROR (code 4)."""
    result = execute_admin_command(collection, {"getClusterParameter": "doesNotExist"})
    assertFailureCode(result, NO_SUCH_KEY_ERROR, msg="Unknown parameter name should fail")


def test_getClusterParameter_unrecognized_field_accepted(collection):
    """Test extra comment field is accepted (MongoDB treats it as generic command field)."""
    result = execute_admin_command(collection, {"getClusterParameter": "*", "comment": "test"})
    assertSuccessPartial(result, {"ok": 1.0}, msg="comment field should be accepted")


# ---------------------------------------------------------------------------
# §6  Undocumented coercion edge cases
# ---------------------------------------------------------------------------


def test_getClusterParameter_array_null_element_rejects(collection):
    """Test array containing null element fails with TYPE_MISMATCH_ERROR."""
    result = execute_admin_command(collection, {"getClusterParameter": [None]})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="Null element in array should be rejected")


def test_getClusterParameter_array_doc_element_rejects(collection):
    """Test array containing a document element fails with TYPE_MISMATCH_ERROR."""
    result = execute_admin_command(collection, {"getClusterParameter": [{"a": 1}]})
    assertFailureCode(
        result, TYPE_MISMATCH_ERROR, msg="Document element in array should be rejected"
    )


def test_getClusterParameter_array_nested_array_rejects(collection):
    """Test array containing a nested array element fails with TYPE_MISMATCH_ERROR."""
    result = execute_admin_command(collection, {"getClusterParameter": [[_VALID_PARAM]]})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="Nested array element should be rejected")


def test_getClusterParameter_array_mixed_valid_unknown_errors(collection):
    """Test array with one valid and one unknown name fails with NO_SUCH_KEY_ERROR."""
    result = execute_admin_command(
        collection, {"getClusterParameter": [_VALID_PARAM, "unknownParam"]}
    )
    assertFailureCode(result, NO_SUCH_KEY_ERROR, msg="Unknown entry in mixed array should fail")


# ---------------------------------------------------------------------------
# §15  Command-document quirks
# ---------------------------------------------------------------------------


def test_getClusterParameter_wrong_case_command_key_rejected(collection):
    """Test wrong-case command key 'getclusterparameter' is rejected as unknown command."""
    result = execute_admin_command(collection, {"getclusterparameter": "*"})
    assertFailureCode(
        result, COMMAND_NOT_FOUND_ERROR, msg="Wrong-case command key should be rejected"
    )
