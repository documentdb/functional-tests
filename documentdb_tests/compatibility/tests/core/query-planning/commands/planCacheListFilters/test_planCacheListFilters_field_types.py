"""Tests for planCacheListFilters command field type acceptance."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

_BSON_TYPE_VALUES = [
    ("document", {"a": 1}),
    ("empty_document", {}),
    ("string", "test"),
    ("int32", 123),
    ("int64", Int64(1)),
    ("double", 1.5),
    ("decimal128", Decimal128("1")),
    ("bool_true", True),
    ("bool_false", False),
    ("null", None),
    ("array", [1, 2]),
    ("empty_array", []),
    ("binary", Binary(b"\x00")),
    ("objectid", ObjectId()),
    ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
    ("regex", Regex(".*")),
    ("timestamp", Timestamp(0, 0)),
    ("code", Code("function(){}")),
    ("minkey", MinKey()),
    ("maxkey", MaxKey()),
]

# Property [Comment Type Acceptance]: the comment field accepts any valid
# BSON type.
LIST_FILTERS_COMMENT_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{tid}",
        command=lambda ctx, v=val: {
            "planCacheListFilters": ctx.collection,
            "comment": v,
        },
        expected={"filters": [], "ok": 1.0},
        msg=f"planCacheListFilters should accept comment of type {tid}",
    )
    for tid, val in _BSON_TYPE_VALUES
]


@pytest.mark.parametrize("test", pytest_params(LIST_FILTERS_COMMENT_TYPE_TESTS))
def test_planCacheListFilters_field_types(database_client, collection, test):
    """Test planCacheListFilters command field type acceptance."""
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
