"""
BSON type element preservation tests for $map expression.

Tests that various BSON types are preserved when mapping over arrays,
including special numeric values and boundary values.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
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
# BSON types preserved via identity map
# ---------------------------------------------------------------------------
BSON_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int64_values",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [Int64(1), Int64(2), Int64(3)]},
        expected=[Int64(1), Int64(2), Int64(3)],
        msg="Should preserve Int64 values",
    ),
    ExpressionTestCase(
        id="decimal128_values",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [Decimal128("1.5"), Decimal128("2.5")]},
        expected=[Decimal128("1.5"), Decimal128("2.5")],
        msg="Should preserve Decimal128 values",
    ),
    ExpressionTestCase(
        id="datetime_values",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
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
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")]},
        expected=[ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")],
        msg="Should preserve ObjectId values",
    ),
    ExpressionTestCase(
        id="binary_values",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [Binary(b"\x01", 0), Binary(b"\x02", 0)]},
        expected=[b"\x01", b"\x02"],
        msg="Should preserve Binary values",
    ),
    ExpressionTestCase(
        id="binary_subtype_preservation",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [Binary(b"\x01", 128), Binary(b"\x02", 128)]},
        expected=[Binary(b"\x01", 128), Binary(b"\x02", 128)],
        msg="Should preserve Binary subtype",
    ),
    ExpressionTestCase(
        id="regex_values",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [Regex("^a", "i"), Regex("^b", "i")]},
        expected=[Regex("^a", "i"), Regex("^b", "i")],
        msg="Should preserve Regex values",
    ),
    ExpressionTestCase(
        id="timestamp_values",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [Timestamp(1, 0), Timestamp(2, 0)]},
        expected=[Timestamp(1, 0), Timestamp(2, 0)],
        msg="Should preserve Timestamp values",
    ),
    ExpressionTestCase(
        id="minkey_maxkey",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [MinKey(), MaxKey()]},
        expected=[MinKey(), MaxKey()],
        msg="Should preserve MinKey/MaxKey values",
    ),
    ExpressionTestCase(
        id="uuid_values",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
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
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [1, "two", Int64(3), Decimal128("4"), True, None, MinKey()]},
        expected=[1, "two", Int64(3), Decimal128("4"), True, None, MinKey()],
        msg="Should preserve mixed BSON types via identity",
    ),
    ExpressionTestCase(
        id="mixed_dates_and_ids",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
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
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=[FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY],
        msg="Should preserve infinity values",
    ),
    ExpressionTestCase(
        id="decimal128_infinity",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY]},
        expected=[DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY],
        msg="Should preserve Decimal128 infinity values",
    ),
    ExpressionTestCase(
        id="boundary_values",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [INT32_MIN, INT32_MAX, INT64_MIN, INT64_MAX]},
        expected=[INT32_MIN, INT32_MAX, INT64_MIN, INT64_MAX],
        msg="Should preserve numeric boundary values",
    ),
    ExpressionTestCase(
        id="negative_zero",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
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
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [Decimal128("1.0"), Decimal128("1.00"), Decimal128("1.000")]},
        expected=[Decimal128("1.0"), Decimal128("1.00"), Decimal128("1.000")],
        msg="Decimal128 trailing zeros preserved",
    ),
    ExpressionTestCase(
        id="decimal128_nan",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": [DECIMAL128_NAN, Decimal128("1")]},
        expected=[DECIMAL128_NAN, Decimal128("1")],
        msg="Decimal128 NaN preserved",
    ),
]

# ---------------------------------------------------------------------------
# BSON type transformations
# ---------------------------------------------------------------------------
BSON_TRANSFORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="multiply_int64",
        expression={"$map": {"input": "$arr", "in": {"$multiply": ["$$this", Int64(2)]}}},
        doc={"arr": [Int64(10), Int64(20), Int64(30)]},
        expected=[Int64(20), Int64(40), Int64(60)],
        msg="$multiply on Int64 should preserve Int64 type",
    ),
    ExpressionTestCase(
        id="add_decimal128",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", Decimal128("0.1")]}}},
        doc={"arr": [Decimal128("1.5"), Decimal128("2.5"), Decimal128("3.5")]},
        expected=[Decimal128("1.6"), Decimal128("2.6"), Decimal128("3.6")],
        msg="$add on Decimal128 should preserve precision",
    ),
    ExpressionTestCase(
        id="type_of_mixed_bson",
        expression={"$map": {"input": "$arr", "in": {"$type": "$$this"}}},
        doc={"arr": [1, "two", Int64(3), Decimal128("4"), True, None]},
        expected=["int", "string", "long", "decimal", "bool", "null"],
        msg="$type on mixed BSON types",
    ),
    ExpressionTestCase(
        id="dateToString_datetime",
        expression={
            "$map": {
                "input": "$arr",
                "in": {"$dateToString": {"format": "%Y-%m-%d", "date": "$$this"}},
            }
        },
        doc={
            "arr": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 6, 15, tzinfo=timezone.utc),
            ]
        },
        expected=["2024-01-01", "2024-06-15"],
        msg="$dateToString on datetime array",
    ),
    ExpressionTestCase(
        id="toString_objectid",
        expression={"$map": {"input": "$arr", "in": {"$toString": "$$this"}}},
        doc={"arr": [ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")]},
        expected=["000000000000000000000001", "000000000000000000000002"],
        msg="$toString on ObjectId array",
    ),
    ExpressionTestCase(
        id="toLong_int_values",
        expression={"$map": {"input": "$arr", "in": {"$toLong": "$$this"}}},
        doc={"arr": [1, 2, 3]},
        expected=[Int64(1), Int64(2), Int64(3)],
        msg="$toLong converts int to Int64",
    ),
    ExpressionTestCase(
        id="toDouble_decimal128",
        expression={"$map": {"input": "$arr", "in": {"$toDouble": "$$this"}}},
        doc={"arr": [Decimal128("1.5"), Decimal128("2.0")]},
        expected=[1.5, 2.0],
        msg="$toDouble on Decimal128 array",
    ),
    ExpressionTestCase(
        id="concat_strings",
        expression={"$map": {"input": "$arr", "in": {"$concat": ["$$this", "!"]}}},
        doc={"arr": ["hello", "world"]},
        expected=["hello!", "world!"],
        msg="$concat on string array",
    ),
    ExpressionTestCase(
        id="add_millis_to_datetime",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", 86400000]}}},
        doc={
            "arr": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 6, 1, tzinfo=timezone.utc),
            ]
        },
        expected=[
            datetime(2024, 1, 2, tzinfo=timezone.utc),
            datetime(2024, 6, 2, tzinfo=timezone.utc),
        ],
        msg="Add one day in millis to datetime array",
    ),
    ExpressionTestCase(
        id="subtract_int64",
        expression={"$map": {"input": "$arr", "in": {"$subtract": ["$$this", Int64(50)]}}},
        doc={"arr": [Int64(100), Int64(200), Int64(300)]},
        expected=[Int64(50), Int64(150), Int64(250)],
        msg="$subtract on Int64 array",
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
    + BSON_TRANSFORM_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_BSON_TESTS))
def test_map_bson_insert(collection, test):
    """Test $map BSON types with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
