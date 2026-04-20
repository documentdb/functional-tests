"""
Tests for $lt numeric boundaries and double precision.

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
        "int32_max_minus1_lt_max",
        expression={"$lt": [INT32_MAX - 1, INT32_MAX]},
        expected=True,
        msg="INT32_MAX-1 < INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_max_self",
        expression={"$lt": [INT32_MAX, INT32_MAX]},
        expected=False,
        msg="INT32_MAX not < INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_min_lt_min_plus1",
        expression={"$lt": [INT32_MIN, INT32_MIN + 1]},
        expected=True,
        msg="INT32_MIN < INT32_MIN+1",
    ),
    ExpressionTestCase(
        "int32_min_self",
        expression={"$lt": [INT32_MIN, INT32_MIN]},
        expected=False,
        msg="INT32_MIN not < INT32_MIN",
    ),
    ExpressionTestCase(
        "int32_max_lt_long_above",
        expression={"$lt": [INT32_MAX, Int64(INT32_MAX + 1)]},
        expected=True,
        msg="int(INT32_MAX) < long(INT32_MAX+1)",
    ),
]


INT64_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_max_minus1_lt_max",
        expression={"$lt": [Int64(INT64_MAX - 1), INT64_MAX]},
        expected=True,
        msg="INT64_MAX-1 < INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_max_self",
        expression={"$lt": [INT64_MAX, INT64_MAX]},
        expected=False,
        msg="INT64_MAX not < INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_min_lt_min_plus1",
        expression={"$lt": [INT64_MIN, Int64(INT64_MIN + 1)]},
        expected=True,
        msg="INT64_MIN < INT64_MIN+1",
    ),
    ExpressionTestCase(
        "int64_min_self",
        expression={"$lt": [INT64_MIN, INT64_MIN]},
        expected=False,
        msg="INT64_MIN not < INT64_MIN",
    ),
]

DOUBLE_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "near_max_self",
        expression={"$lt": [DOUBLE_NEAR_MAX, DOUBLE_NEAR_MAX]},
        expected=False,
        msg="DOUBLE_NEAR_MAX not < itself",
    ),
    ExpressionTestCase(
        "zero_lt_subnormal",
        expression={"$lt": [0.0, DOUBLE_MIN_SUBNORMAL]},
        expected=True,
        msg="0.0 < min subnormal",
    ),
    ExpressionTestCase(
        "subnormal_lt_zero",
        expression={"$lt": [DOUBLE_MIN_SUBNORMAL, 0.0]},
        expected=False,
        msg="min subnormal not < 0.0",
    ),
    ExpressionTestCase(
        "neg_subnormal_lt_zero",
        expression={"$lt": [DOUBLE_MIN_NEGATIVE_SUBNORMAL, 0.0]},
        expected=True,
        msg="neg subnormal < 0.0",
    ),
    ExpressionTestCase(
        "zero_lt_neg_subnormal",
        expression={"$lt": [0.0, DOUBLE_MIN_NEGATIVE_SUBNORMAL]},
        expected=False,
        msg="0.0 not < neg subnormal",
    ),
    ExpressionTestCase(
        "near_min_lt_near_max",
        expression={"$lt": [DOUBLE_NEAR_MIN, DOUBLE_NEAR_MAX]},
        expected=True,
        msg="DOUBLE_NEAR_MIN < DOUBLE_NEAR_MAX",
    ),
]


LARGE_NUMBER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_beyond_double_precision",
        expression={"$lt": [Int64(9007199254740992), Int64(9007199254740993)]},
        expected=True,
        msg="int64 beyond double precision",
    ),
    ExpressionTestCase(
        "dec_34_digit",
        expression={
            "$lt": [
                Decimal128("9999999999999999999999999999999998"),
                Decimal128("9999999999999999999999999999999999"),
            ]
        },
        expected=True,
        msg="34-digit decimal comparison",
    ),
    ExpressionTestCase(
        "int64_max_vs_double_int64_max",
        expression={"$lt": [INT64_MAX, float(INT64_MAX)]},
        expected=True,
        msg="INT64_MAX < double(INT64_MAX) due to precision loss rounding up",
    ),
]


ALL_TESTS = INT32_TESTS + INT64_TESTS + DOUBLE_PRECISION_TESTS + LARGE_NUMBER_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_lt_boundary_precision(collection, test):
    """Test $lt numeric boundaries and double precision."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
