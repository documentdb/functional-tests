"""
Numeric index type tests for $arrayElemAt expression.

Tests various numeric types (Int64, double, Decimal128) and edge cases
like negative zero and Decimal128 scientific notation as index values.
"""

from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    INT64_ZERO,
)

# Property [Numeric Index Types]: $arrayElemAt accepts int32, int64, and integral double indexes.
NUMERIC_INDEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int64_zero_index",
        doc={"arr": [10, 20, 30], "idx": INT64_ZERO},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=10,
        msg="$arrayElemAt should accept Int64 zero index",
    ),
    ExpressionTestCase(
        id="int64_index",
        doc={"arr": [10, 20, 30], "idx": Int64(1)},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=20,
        msg="$arrayElemAt should accept Int64 index",
    ),
    ExpressionTestCase(
        id="double_integral_index",
        doc={"arr": [10, 20, 30], "idx": 2.0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=30,
        msg="$arrayElemAt should accept integral double index",
    ),
    ExpressionTestCase(
        id="decimal128_integral_index",
        doc={"arr": [10, 20, 30], "idx": DECIMAL128_ZERO},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=10,
        msg="$arrayElemAt should accept Decimal128 index",
    ),
    ExpressionTestCase(
        id="int64_negative_index",
        doc={"arr": [10, 20, 30], "idx": Int64(-1)},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=30,
        msg="$arrayElemAt should accept negative Int64 index",
    ),
    ExpressionTestCase(
        id="double_negative_integral",
        doc={"arr": [10, 20, 30], "idx": -2.0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=20,
        msg="$arrayElemAt should accept negative integral double index",
    ),
    ExpressionTestCase(
        id="negative_zero_index",
        doc={"arr": [10, 20, 30], "idx": DOUBLE_NEGATIVE_ZERO},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=10,
        msg="$arrayElemAt should treat -0.0 as index 0",
    ),
    ExpressionTestCase(
        id="decimal128_negative_zero_index",
        doc={"arr": [10, 20, 30], "idx": DECIMAL128_NEGATIVE_ZERO},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=10,
        msg="$arrayElemAt should treat decimal128 -0 as index 0",
    ),
    ExpressionTestCase(
        id="decimal128_trailing_zero",
        doc={"arr": [10, 20, 30], "idx": DECIMAL128_TRAILING_ZERO},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=20,
        msg="$arrayElemAt should accept decimal128 with trailing zero",
    ),
    ExpressionTestCase(
        id="decimal128_subnormal_zero",
        doc={"arr": [10, 20, 30], "idx": Decimal128("0E-6176")},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=10,
        msg="$arrayElemAt should accept decimal128 subnormal zero",
    ),
    ExpressionTestCase(
        id="decimal128_20E_neg1",
        doc={"arr": [10, 20, 30], "idx": Decimal128("20E-1")},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=30,
        msg="$arrayElemAt should accept decimal128 20E-1 as index 2",
    ),
    ExpressionTestCase(
        id="decimal128_0_2E1",
        doc={"arr": [10, 20, 30], "idx": Decimal128("0.2E1")},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=30,
        msg="$arrayElemAt should accept decimal128 0.2E1 as index 2",
    ),
    ExpressionTestCase(
        id="decimal128_2E0",
        doc={"arr": [10, 20, 30], "idx": Decimal128("2E0")},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=30,
        msg="$arrayElemAt should accept decimal128 2E0 as index 2",
    ),
    ExpressionTestCase(
        id="decimal128_10E_neg1",
        doc={"arr": [10, 20, 30], "idx": Decimal128("10E-1")},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=20,
        msg="$arrayElemAt should accept decimal128 10E-1 as index 1",
    ),
    ExpressionTestCase(
        id="decimal128_negative_integral_index",
        doc={"arr": [10, 20, 30], "idx": Decimal128("-1")},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=30,
        msg="$arrayElemAt should accept negative Decimal128 integral index",
    ),
    ExpressionTestCase(
        id="decimal128_neg_10E_neg1",
        doc={"arr": [10, 20, 30], "idx": Decimal128("-10E-1")},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=30,
        msg="$arrayElemAt should accept decimal128 -10E-1 as index -1",
    ),
    ExpressionTestCase(
        id="decimal128_0E_pos3",
        doc={"arr": [10, 20, 30], "idx": Decimal128("0E+3")},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=10,
        msg="$arrayElemAt should accept decimal128 0E+3 as index 0",
    ),
    ExpressionTestCase(
        id="decimal128_0E_neg3",
        doc={"arr": [10, 20, 30], "idx": Decimal128("0E-3")},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=10,
        msg="$arrayElemAt should accept decimal128 0E-3 as index 0",
    ),
    ExpressionTestCase(
        id="decimal128_1_00000",
        doc={"arr": [10, 20, 30], "idx": Decimal128("1.00000")},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=20,
        msg="$arrayElemAt should accept decimal128 1.00000 as index 1",
    ),
]
