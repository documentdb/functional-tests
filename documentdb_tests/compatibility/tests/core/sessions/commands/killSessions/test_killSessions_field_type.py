"""Tests for killSessions command field type rejection."""

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

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
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

# Property [Command Field Type Rejection]: the killSessions command field
# expects an array. All non-array BSON types are rejected.
KILLSESSIONS_FIELD_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"field_type_{tid}",
        command=lambda ctx, v=val: {"killSessions": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killSessions should reject {tid} as command field value",
    )
    for tid, val in [
        ("int32", 1),
        ("int32_zero", 0),
        ("int32_negative", -1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("double_zero", 0.0),
        ("double_negative", -1.0),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
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
        ("double_nan", float("nan")),
        ("double_inf", float("inf")),
    ]
] + [
    # Null produces a missing field error rather than a type mismatch.
    CommandTestCase(
        "field_type_null",
        command=lambda ctx: {"killSessions": None},
        error_code=MISSING_FIELD_ERROR,
        msg="killSessions should reject null as command field value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(KILLSESSIONS_FIELD_TYPE_ERROR_TESTS))
def test_killSessions_field_type(collection, test):
    """Test killSessions command field type rejection."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
