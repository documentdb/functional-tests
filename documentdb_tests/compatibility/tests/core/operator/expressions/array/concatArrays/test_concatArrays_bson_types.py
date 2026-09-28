"""
BSON type element preservation tests for $concatArrays expression.

Tests that various BSON types are preserved when concatenating arrays,
including special numeric values and boundary values.
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

# Property [Type Preservation]: $concatArrays preserves each element's BSON type.
BSON_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int64_values",
        doc={"arr0": [Int64(1), Int64(2)], "arr1": [Int64(3)]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[Int64(1), Int64(2), Int64(3)],
        msg="$concatArrays should preserve Int64 values",
    ),
    ExpressionTestCase(
        id="decimal128_values",
        doc={
            "arr0": [DECIMAL128_ONE_AND_HALF],
            "arr1": [DECIMAL128_TWO_AND_HALF, Decimal128("3.5")],
        },
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[DECIMAL128_ONE_AND_HALF, DECIMAL128_TWO_AND_HALF, Decimal128("3.5")],
        msg="$concatArrays should preserve Decimal128 values",
    ),
    ExpressionTestCase(
        id="datetime_values",
        doc={
            "arr0": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
            "arr1": [datetime(2024, 6, 1, tzinfo=timezone.utc)],
        },
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 6, 1, tzinfo=timezone.utc),
        ],
        msg="$concatArrays should preserve datetime values",
    ),
    ExpressionTestCase(
        id="objectid_values",
        doc={
            "arr0": [ObjectId("000000000000000000000001")],
            "arr1": [ObjectId("000000000000000000000002")],
        },
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[
            ObjectId("000000000000000000000001"),
            ObjectId("000000000000000000000002"),
        ],
        msg="$concatArrays should preserve ObjectId values",
    ),
    ExpressionTestCase(
        id="binary_values",
        doc={"arr0": [Binary(b"\x01", 0)], "arr1": [Binary(b"\x02", 0)]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[b"\x01", b"\x02"],
        msg="$concatArrays should preserve Binary values",
    ),
    ExpressionTestCase(
        id="regex_values",
        doc={"arr0": [Regex("^a", "i")], "arr1": [Regex("^b", "i")]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[Regex("^a", "i"), Regex("^b", "i")],
        msg="$concatArrays should preserve Regex values",
    ),
    ExpressionTestCase(
        id="timestamp_values",
        doc={"arr0": [Timestamp(1, 0)], "arr1": [Timestamp(2, 0)]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[Timestamp(1, 0), Timestamp(2, 0)],
        msg="$concatArrays should preserve Timestamp values",
    ),
    ExpressionTestCase(
        id="minkey_maxkey",
        doc={"arr0": [MinKey()], "arr1": [MaxKey()]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[MinKey(), MaxKey()],
        msg="$concatArrays should preserve MinKey/MaxKey values",
    ),
    ExpressionTestCase(
        id="uuid_values",
        doc={
            "arr0": [Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))],
            "arr1": [Binary.from_uuid(UUID("fedcba98-7654-3210-0123-456789abcdef"))],
        },
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[
            Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")),
            Binary.from_uuid(UUID("fedcba98-7654-3210-0123-456789abcdef")),
        ],
        msg="$concatArrays should preserve UUID binary values",
    ),
]

# Property [Mixed Types]: $concatArrays concatenates arrays holding mixed BSON element types.
MIXED_BSON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="mixed_bson_types",
        doc={"arr0": [1, "two", Int64(3)], "arr1": [Decimal128("4"), True, None, MinKey()]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[1, "two", Int64(3), Decimal128("4"), True, None, MinKey()],
        msg="$concatArrays should concatenate mixed BSON types preserving each",
    ),
    ExpressionTestCase(
        id="mixed_dates_and_ids",
        doc={
            "arr0": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                ObjectId("000000000000000000000001"),
            ],
            "arr1": [Timestamp(1, 0), Binary(b"\x01", 0)],
        },
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            ObjectId("000000000000000000000001"),
            Timestamp(1, 0),
            b"\x01",
        ],
        msg="$concatArrays should concatenate dates, ObjectIds, timestamps, and binary",
    ),
    ExpressionTestCase(
        id="mixed_extremes",
        doc={"arr0": [MinKey(), FLOAT_NEGATIVE_INFINITY, None], "arr1": [FLOAT_INFINITY, MaxKey()]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[MinKey(), FLOAT_NEGATIVE_INFINITY, None, FLOAT_INFINITY, MaxKey()],
        msg="$concatArrays should concatenate MinKey, MaxKey, infinities, and null",
    ),
]

# Property [Special Numerics]: $concatArrays preserves NaN, Infinity, and negative zero elements.
SPECIAL_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="infinity_values",
        doc={"arr0": [FLOAT_INFINITY], "arr1": [FLOAT_NEGATIVE_INFINITY]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY],
        msg="$concatArrays should preserve infinity values",
    ),
    ExpressionTestCase(
        id="decimal128_infinity",
        doc={"arr0": [DECIMAL128_INFINITY], "arr1": [DECIMAL128_NEGATIVE_INFINITY]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY],
        msg="$concatArrays should preserve Decimal128 infinity values",
    ),
    ExpressionTestCase(
        id="boundary_values",
        doc={"arr0": [INT32_MIN, INT32_MAX], "arr1": [INT64_MIN, INT64_MAX]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[INT32_MIN, INT32_MAX, INT64_MIN, INT64_MAX],
        msg="$concatArrays should preserve numeric boundary values",
    ),
    ExpressionTestCase(
        id="negative_zero",
        doc={"arr0": [DOUBLE_NEGATIVE_ZERO], "arr1": [DECIMAL128_NEGATIVE_ZERO]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[DOUBLE_NEGATIVE_ZERO, DECIMAL128_NEGATIVE_ZERO],
        msg="$concatArrays should preserve negative zero values",
    ),
]

# Property [Element Identity]: $concatArrays preserves element values and order.
ELEMENT_PRESERVATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="decimal128_trailing_zeros",
        doc={"arr0": [DECIMAL128_TRAILING_ZERO], "arr1": [Decimal128("1.00"), Decimal128("1.000")]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[DECIMAL128_TRAILING_ZERO, Decimal128("1.00"), Decimal128("1.000")],
        msg="$concatArrays should preserve Decimal128 trailing zeros",
    ),
    ExpressionTestCase(
        id="decimal128_nan",
        doc={"arr0": [DECIMAL128_NAN], "arr1": [Decimal128("1")]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[DECIMAL128_NAN, Decimal128("1")],
        msg="$concatArrays should preserve a Decimal128 NaN element",
    ),
]

ALL_BSON_TESTS = (
    BSON_TYPE_TESTS + MIXED_BSON_TESTS + SPECIAL_NUMERIC_TESTS + ELEMENT_PRESERVATION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_BSON_TESTS))
def test_concatArrays_bson_insert(collection, test):
    """Test $concatArrays BSON types with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
