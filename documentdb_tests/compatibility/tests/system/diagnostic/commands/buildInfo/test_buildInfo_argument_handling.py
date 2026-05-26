"""Tests for buildInfo command argument handling.

Validates that buildInfo accepts any BSON type as its argument value.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin


@dataclass(frozen=True)
class BuildInfoArgTest(BaseTestCase):
    """Test case for buildInfo argument variations."""

    arg_value: Any = None


ARGUMENT_TYPE_TESTS: list[BuildInfoArgTest] = [
    BuildInfoArgTest("int_1", arg_value=1, expected={"ok": 1.0}, msg="Should accept int 1"),
    BuildInfoArgTest("int_0", arg_value=0, expected={"ok": 1.0}, msg="Should accept int 0"),
    BuildInfoArgTest("int_neg1", arg_value=-1, expected={"ok": 1.0}, msg="Should accept int -1"),
    BuildInfoArgTest("bool_true", arg_value=True, expected={"ok": 1.0}, msg="Should accept true"),
    BuildInfoArgTest(
        "bool_false", arg_value=False, expected={"ok": 1.0}, msg="Should accept false"
    ),
    BuildInfoArgTest("string", arg_value="hello", expected={"ok": 1.0}, msg="Should accept string"),
    BuildInfoArgTest("null", arg_value=None, expected={"ok": 1.0}, msg="Should accept null"),
    BuildInfoArgTest(
        "empty_object", arg_value={}, expected={"ok": 1.0}, msg="Should accept empty object"
    ),
    BuildInfoArgTest(
        "empty_array", arg_value=[], expected={"ok": 1.0}, msg="Should accept empty array"
    ),
    BuildInfoArgTest("double", arg_value=1.5, expected={"ok": 1.0}, msg="Should accept double"),
    BuildInfoArgTest("int64", arg_value=Int64(1), expected={"ok": 1.0}, msg="Should accept int64"),
    BuildInfoArgTest(
        "decimal128",
        arg_value=Decimal128("1"),
        expected={"ok": 1.0},
        msg="Should accept decimal128",
    ),
    BuildInfoArgTest(
        "decimal128_nan",
        arg_value=Decimal128("NaN"),
        expected={"ok": 1.0},
        msg="Should accept decimal128 NaN",
    ),
    BuildInfoArgTest(
        "infinity",
        arg_value=float("inf"),
        expected={"ok": 1.0},
        msg="Should accept infinity",
    ),
    BuildInfoArgTest(
        "date",
        arg_value=datetime(2024, 1, 1, tzinfo=timezone.utc),
        expected={"ok": 1.0},
        msg="Should accept date",
    ),
    BuildInfoArgTest(
        "binData", arg_value=Binary(b""), expected={"ok": 1.0}, msg="Should accept binData"
    ),
    BuildInfoArgTest(
        "objectId", arg_value=ObjectId(), expected={"ok": 1.0}, msg="Should accept objectId"
    ),
    BuildInfoArgTest(
        "regex", arg_value=Regex("test"), expected={"ok": 1.0}, msg="Should accept regex"
    ),
    BuildInfoArgTest(
        "timestamp",
        arg_value=Timestamp(0, 0),
        expected={"ok": 1.0},
        msg="Should accept timestamp",
    ),
    BuildInfoArgTest(
        "minKey", arg_value=MinKey(), expected={"ok": 1.0}, msg="Should accept minKey"
    ),
    BuildInfoArgTest(
        "maxKey", arg_value=MaxKey(), expected={"ok": 1.0}, msg="Should accept maxKey"
    ),
    BuildInfoArgTest(
        "code",
        arg_value=Code("function(){}"),
        expected={"ok": 1.0},
        msg="Should accept JavaScript code",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_TYPE_TESTS))
def test_buildInfo_argument_types(collection, test):
    """Test that buildInfo accepts various BSON types as argument value."""
    result = execute_admin_command(collection, {"buildInfo": test.arg_value})
    assertSuccessPartial(result, test.expected, msg=test.msg)
