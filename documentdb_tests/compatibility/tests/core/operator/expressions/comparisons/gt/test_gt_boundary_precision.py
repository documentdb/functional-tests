"""
Tests for $gt numeric boundaries and double precision.

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
        "int32_max_gt_max_minus1",
        expression={"$gt": [INT32_MAX, INT32_MAX - 1]},
        expected=True,
        msg="INT32_MAX > INT32_MAX-1",
    ),
    ExpressionTestCase(
        "int32_max_minus1_not_gt_max",
        expression={"$gt": [INT32_MAX - 1, INT32_MAX]},
        expected=False,
        msg="INT32_MAX-1 not > INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_max_self",
        expression={"$gt": [INT32_MAX, INT32_MAX]},
        expected=False,
        msg="INT32_MAX not > INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_min_plus1_gt_min",
        expression={"$gt": [INT32_MIN + 1, INT32_MIN]},
        expected=True,
        msg="INT32_MIN+1 > INT32_MIN",
    ),
    ExpressionTestCase(
        "int32_min_self",
        expression={"$gt": [INT32_MIN, INT32_MIN]},
        expected=False,
        msg="INT32_MIN not > INT32_MIN",
    ),
    ExpressionTestCase(
        "long_above_int32_gt_int32_max",
        expression={"$gt": [Int64(INT32_MAX + 1), INT32_MAX]},
        expected=True,
        msg="long(INT32_MAX+1) > int(INT32_MAX)",
    ),
    ExpressionTestCase(
        "int32_max_not_gt_long_above",
        expression={"$gt": [INT32_MAX, Int64(INT32_MAX + 1)]},
        expected=False,
        msg="int(INT32_MAX) not > long(INT32_MAX+1)",
    ),
    ExpressionTestCase(
        "long_below_int32_gt_int32_min",
        expression={"$gt": [Int64(INT32_MIN - 1), INT32_MIN]},
        expected=False,
        msg="long(INT32_MIN-1) not > int(INT32_MIN)",
    ),
]

INT64_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_max_gt_max_minus1",
        expression={"$gt": [INT64_MAX, Int64(INT64_MAX - 1)]},
        expected=True,
        msg="INT64_MAX > INT64_MAX-1",
    ),
    ExpressionTestCase(
        "int64_max_self",
        expression={"$gt": [INT64_MAX, INT64_MAX]},
        expected=False,
        msg="INT64_MAX not > INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_min_plus1_gt_min",
        expression={"$gt": [Int64(INT64_MIN + 1), INT64_MIN]},
        expected=True,
        msg="INT64_MIN+1 > INT64_MIN",
    ),
    ExpressionTestCase(
        "int64_min_self",
        expression={"$gt": [INT64_MIN, INT64_MIN]},
        expected=False,
        msg="INT64_MIN not > INT64_MIN",
    ),
]

DOUBLE_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "near_max_self",
        expression={"$gt": [DOUBLE_NEAR_MAX, DOUBLE_NEAR_MAX]},
        expected=False,
        msg="DOUBLE_NEAR_MAX not > itself",
    ),
    ExpressionTestCase(
        "subnormal_gt_zero",
        expression={"$gt": [DOUBLE_MIN_SUBNORMAL, 0.0]},
        expected=True,
        msg="min subnormal > 0.0",
    ),
    ExpressionTestCase(
        "zero_gt_subnormal",
        expression={"$gt": [0.0, DOUBLE_MIN_SUBNORMAL]},
        expected=False,
        msg="0.0 not > min subnormal",
    ),
    ExpressionTestCase(
        "neg_subnormal_gt_zero",
        expression={"$gt": [DOUBLE_MIN_NEGATIVE_SUBNORMAL, 0.0]},
        expected=False,
        msg="neg subnormal not > 0.0",
    ),
    ExpressionTestCase(
        "zero_gt_neg_subnormal",
        expression={"$gt": [0.0, DOUBLE_MIN_NEGATIVE_SUBNORMAL]},
        expected=True,
        msg="0.0 > neg subnormal",
    ),
    ExpressionTestCase(
        "near_min_gt_neg_subnormal",
        expression={"$gt": [DOUBLE_NEAR_MIN, DOUBLE_MIN_NEGATIVE_SUBNORMAL]},
        expected=True,
        msg="DOUBLE_NEAR_MIN > neg subnormal",
    ),
]

LARGE_NUMBER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_beyond_double_precision",
        expression={"$gt": [Int64(9007199254740993), Int64(9007199254740992)]},
        expected=True,
        msg="int64 beyond double precision",
    ),
    ExpressionTestCase(
        "dec_34_digit",
        expression={
            "$gt": [
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
def test_gt_boundary_precision(collection, test):
    """Test $gt boundary values and precision."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
