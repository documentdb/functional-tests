"""
Tests for $gte numeric boundaries and double precision.

Covers INT32/INT64 boundaries, double subnormals, and large number precision edge cases.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

INT32_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max_gte_max_minus1",
        expression={"$gte": [INT32_MAX, INT32_MAX - 1]},
        expected=True,
        msg="INT32_MAX >= INT32_MAX-1",
    ),
    ExpressionTestCase(
        "int32_max_minus1_not_gte_max",
        expression={"$gte": [INT32_MAX - 1, INT32_MAX]},
        expected=False,
        msg="INT32_MAX-1 not >= INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_max_self",
        expression={"$gte": [INT32_MAX, INT32_MAX]},
        expected=True,
        msg="INT32_MAX >= INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_min_plus1_gte_min",
        expression={"$gte": [INT32_MIN + 1, INT32_MIN]},
        expected=True,
        msg="INT32_MIN+1 >= INT32_MIN",
    ),
    ExpressionTestCase(
        "int32_min_self",
        expression={"$gte": [INT32_MIN, INT32_MIN]},
        expected=True,
        msg="INT32_MIN >= INT32_MIN",
    ),
    ExpressionTestCase(
        "long_above_int32_gte_int32_max",
        expression={"$gte": [Int64(INT32_MAX + 1), INT32_MAX]},
        expected=True,
        msg="long(INT32_MAX+1) >= int(INT32_MAX)",
    ),
    ExpressionTestCase(
        "int32_max_not_gte_long_above",
        expression={"$gte": [INT32_MAX, Int64(INT32_MAX + 1)]},
        expected=False,
        msg="int(INT32_MAX) not >= long(INT32_MAX+1)",
    ),
    ExpressionTestCase(
        "long_below_int32_gte_int32_min",
        expression={"$gte": [Int64(INT32_MIN - 1), INT32_MIN]},
        expected=False,
        msg="long(INT32_MIN-1) not >= int(INT32_MIN)",
    ),
]

INT64_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_max_gte_max_minus1",
        expression={"$gte": [INT64_MAX, Int64(INT64_MAX - 1)]},
        expected=True,
        msg="INT64_MAX >= INT64_MAX-1",
    ),
    ExpressionTestCase(
        "int64_max_self",
        expression={"$gte": [INT64_MAX, INT64_MAX]},
        expected=True,
        msg="INT64_MAX >= INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_min_plus1_gte_min",
        expression={"$gte": [Int64(INT64_MIN + 1), INT64_MIN]},
        expected=True,
        msg="INT64_MIN+1 >= INT64_MIN",
    ),
    ExpressionTestCase(
        "int64_min_self",
        expression={"$gte": [INT64_MIN, INT64_MIN]},
        expected=True,
        msg="INT64_MIN >= INT64_MIN",
    ),
]

DOUBLE_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "near_max_self",
        expression={"$gte": [DOUBLE_NEAR_MAX, DOUBLE_NEAR_MAX]},
        expected=True,
        msg="DOUBLE_NEAR_MAX >= itself",
    ),
    ExpressionTestCase(
        "subnormal_gte_zero",
        expression={"$gte": [DOUBLE_MIN_SUBNORMAL, 0.0]},
        expected=True,
        msg="min subnormal >= 0.0",
    ),
    ExpressionTestCase(
        "zero_gte_subnormal",
        expression={"$gte": [0.0, DOUBLE_MIN_SUBNORMAL]},
        expected=False,
        msg="0.0 not >= min subnormal",
    ),
    ExpressionTestCase(
        "neg_subnormal_gte_zero",
        expression={"$gte": [DOUBLE_MIN_NEGATIVE_SUBNORMAL, 0.0]},
        expected=False,
        msg="neg subnormal not >= 0.0",
    ),
    ExpressionTestCase(
        "zero_gte_neg_subnormal",
        expression={"$gte": [0.0, DOUBLE_MIN_NEGATIVE_SUBNORMAL]},
        expected=True,
        msg="0.0 >= neg subnormal",
    ),
    ExpressionTestCase(
        "near_min_gte_neg_subnormal",
        expression={"$gte": [DOUBLE_NEAR_MIN, DOUBLE_MIN_NEGATIVE_SUBNORMAL]},
        expected=True,
        msg="DOUBLE_NEAR_MIN >= neg subnormal",
    ),
]

LARGE_NUMBER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_same",
        expression={"$gte": [Int64(9007199254740993), Int64(9007199254740993)]},
        expected=True,
        msg="int64 beyond double precision self",
    ),
    ExpressionTestCase(
        "int64_beyond_double_precision",
        expression={"$gte": [Int64(9007199254740993), Int64(9007199254740992)]},
        expected=True,
        msg="int64 beyond double precision",
    ),
    ExpressionTestCase(
        "dec_34_digit_self",
        expression={
            "$gte": [
                Decimal128("9999999999999999999999999999999999"),
                Decimal128("9999999999999999999999999999999999"),
            ]
        },
        expected=True,
        msg="34-digit decimal self",
    ),
    ExpressionTestCase(
        "dec_34_digit",
        expression={
            "$gte": [
                Decimal128("9999999999999999999999999999999999"),
                Decimal128("9999999999999999999999999999999998"),
            ]
        },
        expected=True,
        msg="34-digit decimal comparison",
    ),
]

ALL_TESTS = INT32_TESTS + INT64_TESTS + DOUBLE_PRECISION_TESTS + LARGE_NUMBER_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_gte_boundary_precision(collection, test):
    """Test $gte boundary values and precision."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
