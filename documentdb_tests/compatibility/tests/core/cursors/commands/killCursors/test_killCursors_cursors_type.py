"""Tests for killCursors cursors field type rejection."""

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
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [cursors Field Type Rejection]: all non-array types for the
# cursors field are rejected.
KILLCURSORS_CURSORS_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"cursors_type_{tid}",
        command=lambda ctx, v=val: {
            "killCursors": ctx.collection,
            "cursors": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killCursors should reject {tid} as cursors field",
    )
    for tid, val in [
        ("string", "not_an_array"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("bool", True),
        ("object", {"a": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
    ]
]

# Property [cursors Element Type Rejection]: all non-Int64 types inside
# the cursors array are rejected with no numeric coercion.
KILLCURSORS_ELEMENT_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"element_type_{tid}",
        command=lambda ctx, v=val: {
            "killCursors": ctx.collection,
            "cursors": [v],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killCursors should reject {tid} element in cursors array",
    )
    for tid, val in [
        ("int32", 42),
        ("double_whole", 3.0),
        ("double_nan", FLOAT_NAN),
        ("double_infinity", FLOAT_INFINITY),
        ("bool", True),
        ("string", "not_a_cursor"),
        ("object", {"a": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("binary_uuid", Binary(b"\x00" * 16, subtype=4)),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("decimal128", Decimal128("1")),
        ("nested_array", [Int64(1)]),
    ]
] + [
    CommandTestCase(
        "element_type_null_before_invalid",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [None, "bad"],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="killCursors should reject invalid element after null in cursors array",
    ),
    CommandTestCase(
        "element_type_two_nulls_before_invalid",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [None, None, "bad"],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="killCursors should reject invalid element after multiple nulls in cursors array",
    ),
    CommandTestCase(
        "element_type_valid_then_null_then_invalid",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1), None, "bad"],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="killCursors should reject invalid element after valid and null in cursors array",
    ),
    CommandTestCase(
        "element_type_first_element_invalid",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": ["bad", 42],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="killCursors should reject array when first element has wrong type",
    ),
    CommandTestCase(
        "element_type_second_element_invalid",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1), "bad", 42],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="killCursors should reject array when second element has wrong type",
    ),
    CommandTestCase(
        "element_type_multiple_invalid",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(1), 42, "bad"],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="killCursors should reject array with multiple invalid elements",
    ),
]

# Property [cursors Field Missing or Null]: omitting the cursors field
# or setting it to null is rejected because it is a required field.
KILLCURSORS_CURSORS_MISSING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursors_missing_omitted",
        command=lambda ctx: {
            "killCursors": ctx.collection,
        },
        error_code=MISSING_FIELD_ERROR,
        msg="killCursors should reject command when cursors field is omitted",
    ),
    CommandTestCase(
        "cursors_missing_null",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": None,
        },
        error_code=MISSING_FIELD_ERROR,
        msg="killCursors should reject null cursors field as missing",
    ),
]

KILLCURSORS_CURSORS_TYPE_TESTS: list[CommandTestCase] = (
    KILLCURSORS_CURSORS_TYPE_ERROR_TESTS
    + KILLCURSORS_ELEMENT_TYPE_ERROR_TESTS
    + KILLCURSORS_CURSORS_MISSING_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLCURSORS_CURSORS_TYPE_TESTS))
def test_killCursors_cursors_type(collection, test):
    """Test killCursors cursors field type rejection."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
