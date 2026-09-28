"""
BSON type element preservation tests for $filter expression.

Tests that various BSON types are preserved when filtering arrays
(using a cond that keeps all elements), including special numeric values
and boundary values.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# BSON types preserved
BSON_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [Int64(1), Int64(2), Int64(3)]},
        expected=[Int64(1), Int64(2), Int64(3)],
        msg="$filter should preserve Int64 values",
    ),
    ExpressionTestCase(
        "decimal128_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [DECIMAL128_ONE_AND_HALF, DECIMAL128_TWO_AND_HALF]},
        expected=[DECIMAL128_ONE_AND_HALF, DECIMAL128_TWO_AND_HALF],
        msg="$filter should preserve Decimal128 values",
    ),
    ExpressionTestCase(
        "datetime_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={
            "arr": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 6, 1, tzinfo=timezone.utc),
            ]
        },
        expected=[
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 6, 1, tzinfo=timezone.utc),
        ],
        msg="$filter should preserve datetime values",
    ),
    ExpressionTestCase(
        "objectid_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")]},
        expected=[ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")],
        msg="$filter should preserve ObjectId values",
    ),
    ExpressionTestCase(
        "binary_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [Binary(b"\x01", 0), Binary(b"\x02", 0)]},
        expected=[b"\x01", b"\x02"],
        msg="$filter should preserve Binary values",
    ),
    ExpressionTestCase(
        "binary_subtype_preservation",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [Binary(b"\x01", 128), Binary(b"\x02", 128)]},
        expected=[Binary(b"\x01", 128), Binary(b"\x02", 128)],
        msg="$filter should preserve Binary subtype",
    ),
    ExpressionTestCase(
        "regex_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [Regex("^a", "i"), Regex("^b", "i")]},
        expected=[Regex("^a", "i"), Regex("^b", "i")],
        msg="$filter should preserve Regex values",
    ),
    ExpressionTestCase(
        "timestamp_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [Timestamp(1, 0), Timestamp(2, 0)]},
        expected=[Timestamp(1, 0), Timestamp(2, 0)],
        msg="$filter should preserve Timestamp values",
    ),
    ExpressionTestCase(
        "minkey_maxkey",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [MinKey(), MaxKey()]},
        expected=[MinKey(), MaxKey()],
        msg="$filter should preserve MinKey/MaxKey values",
    ),
    ExpressionTestCase(
        "uuid_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={
            "arr": [
                Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")),
                Binary.from_uuid(UUID("fedcba98-7654-3210-0123-456789abcdef")),
            ]
        },
        expected=[
            Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")),
            Binary.from_uuid(UUID("fedcba98-7654-3210-0123-456789abcdef")),
        ],
        msg="$filter should preserve UUID binary values",
    ),
]

# Mixed BSON types
MIXED_BSON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mixed_bson_types",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [1, "two", Int64(3), Decimal128("4"), True, None, MinKey()]},
        expected=[1, "two", Int64(3), Decimal128("4"), True, None, MinKey()],
        msg="$filter should preserve mixed BSON types",
    ),
    ExpressionTestCase(
        "mixed_dates_and_ids",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={
            "arr": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                ObjectId("000000000000000000000001"),
                Timestamp(1, 0),
            ]
        },
        expected=[
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            ObjectId("000000000000000000000001"),
            Timestamp(1, 0),
        ],
        msg="$filter should preserve dates, ObjectIds, timestamps",
    ),
]

# Special numeric values as elements
SPECIAL_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "infinity_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=[FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY],
        msg="$filter should preserve infinity values",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY]},
        expected=[DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY],
        msg="$filter should preserve Decimal128 infinity values",
    ),
    ExpressionTestCase(
        "boundary_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [INT32_MIN, INT32_MAX, INT64_MIN, INT64_MAX]},
        expected=[INT32_MIN, INT32_MAX, INT64_MIN, INT64_MAX],
        msg="$filter should preserve numeric boundary values",
    ),
    ExpressionTestCase(
        "negative_zero",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [DOUBLE_NEGATIVE_ZERO, DECIMAL128_NEGATIVE_ZERO]},
        expected=[DOUBLE_NEGATIVE_ZERO, DECIMAL128_NEGATIVE_ZERO],
        msg="$filter should preserve negative zero values",
    ),
]

# Decimal128 precision preservation
DECIMAL128_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal128_trailing_zeros",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [DECIMAL128_TRAILING_ZERO, Decimal128("1.00"), Decimal128("1.000")]},
        expected=[DECIMAL128_TRAILING_ZERO, Decimal128("1.00"), Decimal128("1.000")],
        msg="$filter decimal128 trailing zeros preserved",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [DECIMAL128_NAN, Decimal128("1")]},
        expected=[DECIMAL128_NAN, Decimal128("1")],
        msg="$filter decimal128 NaN preserved",
    ),
]

# BSON type filtering with $eq condition
BSON_FILTER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "filter_int64",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", Int64(2)]}}},
        doc={"arr": [Int64(1), Int64(2), Int64(3)]},
        expected=[Int64(2)],
        msg="$filter should filter and preserve Int64",
    ),
    ExpressionTestCase(
        "filter_decimal128",
        expression={
            "$filter": {"input": "$arr", "cond": {"$eq": ["$$this", DECIMAL128_TWO_AND_HALF]}}
        },
        doc={"arr": [DECIMAL128_ONE_AND_HALF, DECIMAL128_TWO_AND_HALF]},
        expected=[DECIMAL128_TWO_AND_HALF],
        msg="$filter should filter and preserve Decimal128",
    ),
    ExpressionTestCase(
        "filter_datetime",
        expression={
            "$filter": {
                "input": "$arr",
                "cond": {"$eq": ["$$this", datetime(2024, 6, 1, tzinfo=timezone.utc)]},
            }
        },
        doc={
            "arr": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 6, 1, tzinfo=timezone.utc),
            ]
        },
        expected=[datetime(2024, 6, 1, tzinfo=timezone.utc)],
        msg="$filter should filter and preserve datetime",
    ),
    ExpressionTestCase(
        "filter_objectid",
        expression={
            "$filter": {
                "input": "$arr",
                "cond": {"$eq": ["$$this", ObjectId("000000000000000000000001")]},
            }
        },
        doc={"arr": [ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")]},
        expected=[ObjectId("000000000000000000000001")],
        msg="$filter should filter and preserve ObjectId",
    ),
    ExpressionTestCase(
        "filter_binary_subtype",
        expression={
            "$filter": {"input": "$arr", "cond": {"$eq": ["$$this", Binary(b"\x02", 128)]}}
        },
        doc={"arr": [Binary(b"\x01", 128), Binary(b"\x02", 128)]},
        expected=[Binary(b"\x02", 128)],
        msg="$filter should filter and preserve Binary subtype",
    ),
    ExpressionTestCase(
        "filter_timestamp",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", Timestamp(2, 0)]}}},
        doc={"arr": [Timestamp(1, 0), Timestamp(2, 0)]},
        expected=[Timestamp(2, 0)],
        msg="$filter should filter and preserve Timestamp",
    ),
    ExpressionTestCase(
        "filter_regex",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", Regex("^b", "i")]}}},
        doc={"arr": [Regex("^a", "i"), Regex("^b", "i")]},
        expected=[Regex("^b", "i")],
        msg="$filter should filter and preserve Regex",
    ),
    ExpressionTestCase(
        "filter_minkey",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", MinKey()]}}},
        doc={"arr": [MinKey(), MaxKey()]},
        expected=[MinKey()],
        msg="$filter should filter and preserve MinKey",
    ),
    ExpressionTestCase(
        "filter_decimal128_nan_not_gte",
        expression={"$filter": {"input": "$arr", "cond": {"$gte": ["$$this", 1]}}},
        doc={"arr": [DECIMAL128_NAN]},
        expected=[],
        msg="$filter decimal128 NaN not >= 1",
    ),
    ExpressionTestCase(
        "filter_decimal128_neg_inf_not_gte",
        expression={"$filter": {"input": "$arr", "cond": {"$gte": ["$$this", 1]}}},
        doc={"arr": [DECIMAL128_NEGATIVE_INFINITY]},
        expected=[],
        msg="$filter decimal128 -Infinity not >= 1",
    ),
    ExpressionTestCase(
        "filter_decimal128_inf_gte",
        expression={"$filter": {"input": "$arr", "cond": {"$gte": ["$$this", 1]}}},
        doc={"arr": [DECIMAL128_INFINITY]},
        expected=[DECIMAL128_INFINITY],
        msg="$filter decimal128 Infinity >= 1",
    ),
]

# Aggregate and test
ALL_BSON_TESTS = (
    BSON_TYPE_TESTS
    + MIXED_BSON_TESTS
    + SPECIAL_NUMERIC_TESTS
    + DECIMAL128_PRECISION_TESTS
    + BSON_FILTER_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_BSON_TESTS))
def test_filter_bson_insert(collection, test):
    """Test $filter BSON types with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
