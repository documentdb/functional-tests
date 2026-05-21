"""Tests for aggregate command collation strength sub-field rejection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_OVERFLOW,
)

# Property [Strength Type and Range Errors]: non-numeric types produce
# TYPE_MISMATCH_ERROR, and out-of-range values, NaN, infinity, and negative
# zero produce BAD_VALUE_ERROR.
COLLATION_STRENGTH_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "strength_type_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": "high"},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject string strength",
    ),
    CommandTestCase(
        "strength_type_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject boolean strength",
    ),
    CommandTestCase(
        "strength_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": [1]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array strength",
    ),
    CommandTestCase(
        "strength_type_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": {"value": 1}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject object strength",
    ),
    CommandTestCase(
        "strength_type_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject ObjectId strength",
    ),
    CommandTestCase(
        "strength_type_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": datetime(2021, 1, 1, tzinfo=timezone.utc)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject datetime strength",
    ),
    CommandTestCase(
        "strength_type_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": Timestamp(1, 1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Timestamp strength",
    ),
    CommandTestCase(
        "strength_type_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": Binary(b"x")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Binary strength",
    ),
    CommandTestCase(
        "strength_type_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": Regex(".*")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Regex strength",
    ),
    CommandTestCase(
        "strength_type_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject Code strength",
    ),
    CommandTestCase(
        "strength_type_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject CodeWithScope strength",
    ),
    CommandTestCase(
        "strength_type_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MinKey strength",
    ),
    CommandTestCase(
        "strength_type_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject MaxKey strength",
    ),
    CommandTestCase(
        "strength_out_of_range_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": 0},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject strength 0 as out of range",
    ),
    CommandTestCase(
        "strength_out_of_range_six",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": 6},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject strength 6 as out of range",
    ),
    CommandTestCase(
        "strength_out_of_range_negative",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": -1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative strength",
    ),
    CommandTestCase(
        "strength_out_of_range_large",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": 99},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject strength 99 as out of range",
    ),
    CommandTestCase(
        "strength_int64_exceeds_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": Int64(INT32_OVERFLOW)},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should clamp large Int64 to INT32_MAX before range checking",
    ),
    CommandTestCase(
        "strength_fractional_double_truncated_to_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": 0.9},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should truncate double 0.9 to 0 and reject as out of range",
    ),
    CommandTestCase(
        "strength_decimal128_bankers_rounding_to_six",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": Decimal128("5.5")},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should round Decimal128 5.5 to 6 and reject as out of range",
    ),
    CommandTestCase(
        "strength_nan_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": FLOAT_NAN},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should convert double NaN to 0 and reject as out of range",
    ),
    CommandTestCase(
        "strength_nan_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": Decimal128("NaN")},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should convert Decimal128 NaN to 0 and reject as out of range",
    ),
    CommandTestCase(
        "strength_positive_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": FLOAT_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject positive infinity strength",
    ),
    CommandTestCase(
        "strength_negative_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": FLOAT_NEGATIVE_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative infinity strength",
    ),
    CommandTestCase(
        "strength_negative_zero_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": DOUBLE_NEGATIVE_ZERO},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should convert negative zero to 0 and reject as out of range",
    ),
    CommandTestCase(
        "strength_negative_zero_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": DECIMAL128_NEGATIVE_ZERO},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should convert Decimal128 negative zero to 0 and reject as out of range",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_STRENGTH_ERROR_TESTS))
def test_aggregate_collation_strength_rejection(database_client, collection, test):
    """Test aggregate command collation sub-field rejection."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
