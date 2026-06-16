"""Tests for killAllSessions command field type rejection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.no_parallel

# Property [Command Field Type Rejection]: the killAllSessions command
# field expects an array. All non-array BSON types are rejected.
KILLALLSESSIONS_FIELD_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"field_type_{tid}",
        command=lambda ctx, v=val: {"killAllSessions": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killAllSessions should reject {tid} as command field value",
    )
    for tid, val in [
        ("int32_positive", 1),
        ("int32_zero", 0),
        ("int32_negative", -1),
        ("int64", Int64(1)),
        ("int64_max", Int64(9223372036854775807)),
        ("double", 1.0),
        ("double_zero", 0.0),
        ("double_negative", -1.0),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("nan", float("nan")),
        ("infinity", float("inf")),
        ("string", "test"),
        ("string_empty", ""),
        ("object_empty", {}),
        ("object", {"key": "value"}),
        ("binary", Binary(b"\x00\x01\x02")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*", "i")),
        ("timestamp", Timestamp(1, 1)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
] + [
    # Null produces a missing field error rather than a type mismatch.
    CommandTestCase(
        "field_type_null",
        command=lambda ctx: {"killAllSessions": None},
        error_code=MISSING_FIELD_ERROR,
        msg="killAllSessions should reject null as command field value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(KILLALLSESSIONS_FIELD_TYPE_ERROR_TESTS))
def test_killAllSessions_field_type(collection, test):
    """Test killAllSessions command field type rejection."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
