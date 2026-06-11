"""Tests for getMore field type validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    CursorCommandContext,
    CursorCommandTestCase,
    open_find_cursors,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Cursor ID Type Strictness]: only int64 (long) is accepted for the
# getMore field; all other BSON types produce TYPE_MISMATCH_ERROR with no
# numeric coercion.
GETMORE_CURSOR_ID_TYPE_STRICTNESS_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        f"cursor_id_type_{tid}",
        cursor_count=0,
        command=lambda ctx, v=val: {"getMore": v, "collection": ctx.collection},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"getMore should reject {tid} cursor ID",
    )
    for tid, val in [
        ("int32", 42),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("string", "123"),
        ("array", [Int64(1)]),
        ("object", {"id": Int64(1)}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2023, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Collection Type Error]: all non-string, non-null types for the
# collection field produce TYPE_MISMATCH_ERROR.
GETMORE_COLLECTION_TYPE_ERROR_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        f"collection_type_{tid}",
        cursor_count=0,
        command=lambda ctx, v=val: {"getMore": Int64(1), "collection": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"getMore should reject {tid} collection field",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", ["test"]),
        ("object", {"name": "test"}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2023, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [batchSize Type Error]: non-numeric types for batchSize produce
# TYPE_MISMATCH_ERROR; only int32, int64, double, Decimal128, and null are
# accepted.
GETMORE_BATCH_SIZE_TYPE_ERROR_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        f"batch_size_type_{tid}",
        cursor_count=0,
        command=lambda ctx, v=val: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "batchSize": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"getMore should reject {tid} batchSize",
    )
    for tid, val in [
        ("bool", True),
        ("string", "1"),
        ("array", [1]),
        ("object", {"n": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2023, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [maxTimeMS Type Error]: non-numeric types for maxTimeMS produce
# TYPE_MISMATCH_ERROR; only int32, int64, double, Decimal128, and null are
# accepted.
GETMORE_MAX_TIME_MS_TYPE_ERROR_TESTS: list[CursorCommandTestCase] = [
    CursorCommandTestCase(
        f"max_time_ms_type_{tid}",
        cursor_count=0,
        command=lambda ctx, v=val: {
            "getMore": Int64(1),
            "collection": ctx.collection,
            "maxTimeMS": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"getMore should reject {tid} maxTimeMS",
    )
    for tid, val in [
        ("bool", True),
        ("string", "100"),
        ("array", [100]),
        ("object", {"ms": 100}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2023, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

GETMORE_FIELD_TYPE_ERROR_TESTS = (
    GETMORE_CURSOR_ID_TYPE_STRICTNESS_TESTS
    + GETMORE_COLLECTION_TYPE_ERROR_TESTS
    + GETMORE_BATCH_SIZE_TYPE_ERROR_TESTS
    + GETMORE_MAX_TIME_MS_TYPE_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(GETMORE_FIELD_TYPE_ERROR_TESTS))
def test_getMore_field_type_errors(collection, test_case: CursorCommandTestCase):
    """Test getMore field type validation."""
    collection.insert_many([{"_id": i, "v": i} for i in range(5)])
    cursors = open_find_cursors(
        collection, test_case.cursor_count, batch_size=test_case.find_batch_size
    )
    ctx = CursorCommandContext.from_collection(collection, cursors=cursors)
    result = execute_command(collection, test_case.build_command(ctx))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=True,
    )
