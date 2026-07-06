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
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# ---------------------------------------------------------------------------
# BSON types preserved
# ---------------------------------------------------------------------------
BSON_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int64_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [Int64(1), Int64(2), Int64(3)]},
        expected=[Int64(1), Int64(2), Int64(3)],
        msg="Should preserve Int64 values",
    ),
    ExpressionTestCase(
        id="decimal128_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [Decimal128("1.5"), Decimal128("2.5")]},
        expected=[Decimal128("1.5"), Decimal128("2.5")],
        msg="Should preserve Decimal128 values",
    ),
    ExpressionTestCase(
        id="datetime_values",
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
        msg="Should preserve datetime values",
    ),
    ExpressionTestCase(
        id="objectid_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")]},
        expected=[ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")],
        msg="Should preserve ObjectId values",
    ),
    ExpressionTestCase(
        id="binary_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [Binary(b"\x01", 0), Binary(b"\x02", 0)]},
        expected=[b"\x01", b"\x02"],
        msg="Should preserve Binary values",
    ),
    ExpressionTestCase(
        id="binary_subtype_preservation",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [Binary(b"\x01", 128), Binary(b"\x02", 128)]},
        expected=[Binary(b"\x01", 128), Binary(b"\x02", 128)],
        msg="Should preserve Binary subtype",
    ),
    ExpressionTestCase(
        id="regex_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [Regex("^a", "i"), Regex("^b", "i")]},
        expected=[Regex("^a", "i"), Regex("^b", "i")],
        msg="Should preserve Regex values",
    ),
    ExpressionTestCase(
        id="timestamp_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [Timestamp(1, 0), Timestamp(2, 0)]},
        expected=[Timestamp(1, 0), Timestamp(2, 0)],
        msg="Should preserve Timestamp values",
    ),
    ExpressionTestCase(
        id="minkey_maxkey",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [MinKey(), MaxKey()]},
        expected=[MinKey(), MaxKey()],
        msg="Should preserve MinKey/MaxKey values",
    ),
    ExpressionTestCase(
        id="uuid_values",
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
        msg="Should preserve UUID binary values",
    ),
]

# ---------------------------------------------------------------------------
# Mixed BSON types
# ---------------------------------------------------------------------------
MIXED_BSON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="mixed_bson_types",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [1, "two", Int64(3), Decimal128("4"), True, None, MinKey()]},
        expected=[1, "two", Int64(3), Decimal128("4"), True, None, MinKey()],
        msg="Should preserve mixed BSON types",
    ),
    ExpressionTestCase(
        id="mixed_dates_and_ids",
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
        msg="Should preserve dates, ObjectIds, timestamps",
    ),
]

# ---------------------------------------------------------------------------
# Special numeric values as elements
# ---------------------------------------------------------------------------
SPECIAL_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="infinity_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=[FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY],
        msg="Should preserve infinity values",
    ),
    ExpressionTestCase(
        id="decimal128_infinity",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY]},
        expected=[DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY],
        msg="Should preserve Decimal128 infinity values",
    ),
    ExpressionTestCase(
        id="boundary_values",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [INT32_MIN, INT32_MAX, INT64_MIN, INT64_MAX]},
        expected=[INT32_MIN, INT32_MAX, INT64_MIN, INT64_MAX],
        msg="Should preserve numeric boundary values",
    ),
    ExpressionTestCase(
        id="negative_zero",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [DOUBLE_NEGATIVE_ZERO, DECIMAL128_NEGATIVE_ZERO]},
        expected=[DOUBLE_NEGATIVE_ZERO, DECIMAL128_NEGATIVE_ZERO],
        msg="Should preserve negative zero values",
    ),
]

# ---------------------------------------------------------------------------
# Decimal128 precision preservation
# ---------------------------------------------------------------------------
DECIMAL128_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="decimal128_trailing_zeros",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [Decimal128("1.0"), Decimal128("1.00"), Decimal128("1.000")]},
        expected=[Decimal128("1.0"), Decimal128("1.00"), Decimal128("1.000")],
        msg="Decimal128 trailing zeros preserved",
    ),
    ExpressionTestCase(
        id="decimal128_nan",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [DECIMAL128_NAN, Decimal128("1")]},
        expected=[DECIMAL128_NAN, Decimal128("1")],
        msg="Decimal128 NaN preserved",
    ),
]

# ---------------------------------------------------------------------------
# BSON type filtering with $eq condition
# ---------------------------------------------------------------------------
BSON_FILTER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="filter_int64",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", Int64(2)]}}},
        doc={"arr": [Int64(1), Int64(2), Int64(3)]},
        expected=[Int64(2)],
        msg="Should filter and preserve Int64",
    ),
    ExpressionTestCase(
        id="filter_decimal128",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", Decimal128("2.5")]}}},
        doc={"arr": [Decimal128("1.5"), Decimal128("2.5")]},
        expected=[Decimal128("2.5")],
        msg="Should filter and preserve Decimal128",
    ),
    ExpressionTestCase(
        id="filter_datetime",
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
        msg="Should filter and preserve datetime",
    ),
    ExpressionTestCase(
        id="filter_objectid",
        expression={
            "$filter": {
                "input": "$arr",
                "cond": {"$eq": ["$$this", ObjectId("000000000000000000000001")]},
            }
        },
        doc={"arr": [ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")]},
        expected=[ObjectId("000000000000000000000001")],
        msg="Should filter and preserve ObjectId",
    ),
    ExpressionTestCase(
        id="filter_binary_subtype",
        expression={
            "$filter": {"input": "$arr", "cond": {"$eq": ["$$this", Binary(b"\x02", 128)]}}
        },
        doc={"arr": [Binary(b"\x01", 128), Binary(b"\x02", 128)]},
        expected=[Binary(b"\x02", 128)],
        msg="Should filter and preserve Binary subtype",
    ),
    ExpressionTestCase(
        id="filter_timestamp",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", Timestamp(2, 0)]}}},
        doc={"arr": [Timestamp(1, 0), Timestamp(2, 0)]},
        expected=[Timestamp(2, 0)],
        msg="Should filter and preserve Timestamp",
    ),
    ExpressionTestCase(
        id="filter_regex",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", Regex("^b", "i")]}}},
        doc={"arr": [Regex("^a", "i"), Regex("^b", "i")]},
        expected=[Regex("^b", "i")],
        msg="Should filter and preserve Regex",
    ),
    ExpressionTestCase(
        id="filter_minkey",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", MinKey()]}}},
        doc={"arr": [MinKey(), MaxKey()]},
        expected=[MinKey()],
        msg="Should filter and preserve MinKey",
    ),
    ExpressionTestCase(
        id="filter_decimal128_nan_not_gte",
        expression={"$filter": {"input": "$arr", "cond": {"$gte": ["$$this", 1]}}},
        doc={"arr": [Decimal128("NaN")]},
        expected=[],
        msg="Decimal128 NaN not >= 1",
    ),
    ExpressionTestCase(
        id="filter_decimal128_neg_inf_not_gte",
        expression={"$filter": {"input": "$arr", "cond": {"$gte": ["$$this", 1]}}},
        doc={"arr": [Decimal128("-Infinity")]},
        expected=[],
        msg="Decimal128 -Infinity not >= 1",
    ),
    ExpressionTestCase(
        id="filter_decimal128_inf_gte",
        expression={"$filter": {"input": "$arr", "cond": {"$gte": ["$$this", 1]}}},
        doc={"arr": [Decimal128("Infinity")]},
        expected=[Decimal128("Infinity")],
        msg="Decimal128 Infinity >= 1",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
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
