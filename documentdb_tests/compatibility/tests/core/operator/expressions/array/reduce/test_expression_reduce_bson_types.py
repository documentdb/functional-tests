"""
BSON type element tests for $reduce expression.

Most cases use identity reduction (concatArrays into an accumulator array) to verify
BSON element-type preservation, including special numeric and boundary values; the
typed-sum cases instead verify that $add preserves the correct output BSON type.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

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
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [Type Preservation]: $reduce preserves each element's BSON type via identity reduction.
BSON_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_values",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [Int64(1), Int64(2), Int64(3)]},
        expected=[Int64(1), Int64(2), Int64(3)],
        msg="$reduce should preserve Int64 element values",
    ),
    ExpressionTestCase(
        "decimal128_values",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [DECIMAL128_ONE_AND_HALF, DECIMAL128_TWO_AND_HALF]},
        expected=[DECIMAL128_ONE_AND_HALF, DECIMAL128_TWO_AND_HALF],
        msg="$reduce should preserve Decimal128 element values",
    ),
    ExpressionTestCase(
        "datetime_values",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
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
        msg="$reduce should preserve datetime element values",
    ),
    ExpressionTestCase(
        "objectid_values",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")]},
        expected=[ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")],
        msg="$reduce should preserve ObjectId element values",
    ),
    ExpressionTestCase(
        "binary_values",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [Binary(b"\x01", 0), Binary(b"\x02", 0)]},
        expected=[b"\x01", b"\x02"],
        msg="$reduce should preserve Binary element values",
    ),
    ExpressionTestCase(
        "binary_subtype_preservation",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [Binary(b"\x01", 128), Binary(b"\x02", 128)]},
        expected=[Binary(b"\x01", 128), Binary(b"\x02", 128)],
        msg="$reduce should preserve the Binary subtype",
    ),
    ExpressionTestCase(
        "regex_values",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [Regex("^a", "i"), Regex("^b", "i")]},
        expected=[Regex("^a", "i"), Regex("^b", "i")],
        msg="$reduce should preserve Regex element values",
    ),
    ExpressionTestCase(
        "javascript_values",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [Code("a"), Code("b")]},
        expected=[Code("a"), Code("b")],
        msg="$reduce should preserve JavaScript code element values",
    ),
    ExpressionTestCase(
        "timestamp_values",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [Timestamp(1, 0), Timestamp(2, 0)]},
        expected=[Timestamp(1, 0), Timestamp(2, 0)],
        msg="$reduce should preserve Timestamp element values",
    ),
    ExpressionTestCase(
        "minkey_maxkey",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [MinKey(), MaxKey()]},
        expected=[MinKey(), MaxKey()],
        msg="$reduce should preserve MinKey and MaxKey element values",
    ),
    ExpressionTestCase(
        "uuid_values",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
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
        msg="$reduce should preserve UUID Binary element values",
    ),
]

# Property [Mixed Types]: $reduce preserves elements of mixed BSON types.
MIXED_BSON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mixed_bson_types",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [1, "two", Int64(3), Decimal128("4"), True, None, MinKey()]},
        expected=[1, "two", Int64(3), Decimal128("4"), True, None, MinKey()],
        msg="$reduce should preserve mixed BSON types",
    ),
]

# Property [Special Numeric Elements]: $reduce preserves Infinity, NaN, INT32/INT64
# boundary values, and negative-zero elements.
SPECIAL_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "float_nan_values",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [FLOAT_NAN, 1]},
        expected=[pytest.approx(FLOAT_NAN, nan_ok=True), 1],
        msg="$reduce should preserve float NaN values",
    ),
    ExpressionTestCase(
        "infinity_values",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=[FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY],
        msg="$reduce should preserve infinity values",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY]},
        expected=[DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY],
        msg="$reduce should preserve Decimal128 infinity values",
    ),
    ExpressionTestCase(
        "boundary_values",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [INT32_MIN, INT32_MAX, INT64_MIN, INT64_MAX]},
        expected=[INT32_MIN, INT32_MAX, INT64_MIN, INT64_MAX],
        msg="$reduce should preserve numeric boundary values",
    ),
    ExpressionTestCase(
        "negative_zero",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [DOUBLE_NEGATIVE_ZERO, DECIMAL128_NEGATIVE_ZERO]},
        expected=[DOUBLE_NEGATIVE_ZERO, DECIMAL128_NEGATIVE_ZERO],
        msg="$reduce should preserve negative zero values",
    ),
]

# Property [Decimal128 Precision]: $reduce preserves Decimal128 precision and special values.
DECIMAL128_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal128_trailing_zeros",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [DECIMAL128_TRAILING_ZERO, Decimal128("1.00"), Decimal128("1.000")]},
        expected=[DECIMAL128_TRAILING_ZERO, Decimal128("1.00"), Decimal128("1.000")],
        msg="$reduce should preserve Decimal128 trailing zeros",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": [],
                "in": {"$concatArrays": ["$$value", ["$$this"]]},
            }
        },
        doc={"arr": [DECIMAL128_NAN, Decimal128("1")]},
        expected=[DECIMAL128_NAN, Decimal128("1")],
        msg="$reduce should preserve Decimal128 NaN",
    ),
]

# Property [Typed Sum]: $reduce sums numeric elements preserving the result BSON type.
BSON_SUM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sum_int64",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": INT64_ZERO,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [Int64(10), Int64(20), Int64(30)]},
        expected=Int64(60),
        msg="$reduce should sum Int64 values",
    ),
    ExpressionTestCase(
        "sum_decimal128",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": DECIMAL128_ZERO,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [DECIMAL128_ONE_AND_HALF, DECIMAL128_TWO_AND_HALF, Decimal128("3.0")]},
        expected=Decimal128("7.0"),
        msg="$reduce should sum Decimal128 values preserving precision",
    ),
    ExpressionTestCase(
        "sum_double",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": DOUBLE_ZERO,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [1.5, 2.5, 3.0]},
        expected=7.0,
        msg="$reduce should sum double values",
    ),
]

ALL_BSON_TESTS = (
    BSON_TYPE_TESTS
    + MIXED_BSON_TESTS
    + SPECIAL_NUMERIC_TESTS
    + DECIMAL128_PRECISION_TESTS
    + BSON_SUM_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_BSON_TESTS))
def test_reduce_bson_insert(collection, test):
    """Test $reduce BSON types with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
