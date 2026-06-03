"""Tests for startSession command field type acceptance."""

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
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Field Type Acceptance]: the command field accepts any BSON type.
STARTSESSION_FIELD_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"field_type_{tid}",
        command=lambda ctx, v=val: {"startSession": v},
        expected={"ok": Eq(1.0)},
        msg=f"startSession should accept {tid} as command field value",
    )
    for tid, val in [
        ("int32_positive", 1),
        ("int32_negative", -1),
        ("int32_zero", 0),
        ("int64", Int64(1)),
        ("int64_max", Int64(9223372036854775807)),
        ("double", 1.0),
        ("double_negative", -1.0),
        ("double_zero", 0.0),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("nan", float("nan")),
        ("infinity", float("inf")),
        ("string", "test"),
        ("empty_string", ""),
        ("null", None),
        ("empty_object", {}),
        ("non_empty_object", {"key": "value"}),
        ("empty_array", []),
        ("non_empty_array", [1, 2]),
        ("binary", Binary(b"\x00\x01\x02")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*", "i")),
        ("timestamp", Timestamp(1, 1)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_FIELD_TYPE_TESTS))
def test_startSession_field_types(database_client, collection, test):
    """Test startSession command field type acceptance."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
