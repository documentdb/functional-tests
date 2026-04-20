"""
Tests for $gt NaN and Infinity handling.

Covers Infinity comparisons.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_NEAR_MAX,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

INF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "inf_gt_1", expression={"$gt": [FLOAT_INFINITY, 1]}, expected=True, msg="Inf > 1"
    ),
    ExpressionTestCase(
        "1_gt_inf", expression={"$gt": [1, FLOAT_INFINITY]}, expected=False, msg="1 not > Inf"
    ),
    ExpressionTestCase(
        "neg_inf_gt_1",
        expression={"$gt": [FLOAT_NEGATIVE_INFINITY, 1]},
        expected=False,
        msg="-Inf not > 1",
    ),
    ExpressionTestCase(
        "1_gt_neg_inf",
        expression={"$gt": [1, FLOAT_NEGATIVE_INFINITY]},
        expected=True,
        msg="1 > -Inf",
    ),
    ExpressionTestCase(
        "inf_gt_neg_inf",
        expression={"$gt": [FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=True,
        msg="Inf > -Inf",
    ),
    ExpressionTestCase(
        "neg_inf_gt_inf",
        expression={"$gt": [FLOAT_NEGATIVE_INFINITY, FLOAT_INFINITY]},
        expected=False,
        msg="-Inf not > Inf",
    ),
    ExpressionTestCase(
        "inf_self",
        expression={"$gt": [FLOAT_INFINITY, FLOAT_INFINITY]},
        expected=False,
        msg="Inf not > Inf",
    ),
    ExpressionTestCase(
        "neg_inf_self",
        expression={"$gt": [FLOAT_NEGATIVE_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=False,
        msg="-Inf not > -Inf",
    ),
    ExpressionTestCase(
        "inf_gt_near_max",
        expression={"$gt": [FLOAT_INFINITY, DOUBLE_NEAR_MAX]},
        expected=True,
        msg="Inf > DOUBLE_NEAR_MAX",
    ),
]


NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_gt_int", expression={"$gt": [FLOAT_NAN, 1]}, expected=False, msg="NaN not > int"
    ),
    ExpressionTestCase(
        "int_gt_nan", expression={"$gt": [1, FLOAT_NAN]}, expected=True, msg="int > NaN"
    ),
    ExpressionTestCase(
        "nan_gt_inf",
        expression={"$gt": [FLOAT_NAN, FLOAT_INFINITY]},
        expected=False,
        msg="NaN not > Infinity",
    ),
]

ALL_TESTS = INF_TESTS + NAN_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_gt_nan_infinity(collection, test):
    """Test $gt NaN and Infinity handling."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
