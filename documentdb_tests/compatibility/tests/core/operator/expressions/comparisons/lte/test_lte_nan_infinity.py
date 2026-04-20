"""
Tests for $lte Infinity handling.

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
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
)

INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "inf_lte_inf",
        expression={"$lte": [FLOAT_INFINITY, FLOAT_INFINITY]},
        expected=True,
        msg="Infinity <= Infinity",
    ),
    ExpressionTestCase(
        "neg_inf_lte_neg_inf",
        expression={"$lte": [FLOAT_NEGATIVE_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=True,
        msg="-Infinity <= -Infinity",
    ),
    ExpressionTestCase(
        "neg_inf_lte_inf",
        expression={"$lte": [FLOAT_NEGATIVE_INFINITY, FLOAT_INFINITY]},
        expected=True,
        msg="-Infinity <= Infinity",
    ),
    ExpressionTestCase(
        "inf_lte_neg_inf",
        expression={"$lte": [FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=False,
        msg="Infinity not <= -Infinity",
    ),
    ExpressionTestCase(
        "inf_lte_0",
        expression={"$lte": [FLOAT_INFINITY, 0]},
        expected=False,
        msg="Infinity not <= 0",
    ),
    ExpressionTestCase(
        "0_lte_inf", expression={"$lte": [0, FLOAT_INFINITY]}, expected=True, msg="0 <= Infinity"
    ),
    ExpressionTestCase(
        "inf_lte_1",
        expression={"$lte": [FLOAT_INFINITY, 1]},
        expected=False,
        msg="Infinity not <= 1",
    ),
    ExpressionTestCase(
        "1_lte_inf", expression={"$lte": [1, FLOAT_INFINITY]}, expected=True, msg="1 <= Infinity"
    ),
    ExpressionTestCase(
        "neg_inf_lte_0",
        expression={"$lte": [FLOAT_NEGATIVE_INFINITY, 0]},
        expected=True,
        msg="-Infinity <= 0",
    ),
    ExpressionTestCase(
        "0_lte_neg_inf",
        expression={"$lte": [0, FLOAT_NEGATIVE_INFINITY]},
        expected=False,
        msg="0 not <= -Infinity",
    ),
    ExpressionTestCase(
        "inf_lte_int32_max",
        expression={"$lte": [FLOAT_INFINITY, INT32_MAX]},
        expected=False,
        msg="Infinity not <= INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_max_lte_inf",
        expression={"$lte": [INT32_MAX, FLOAT_INFINITY]},
        expected=True,
        msg="INT32_MAX <= Infinity",
    ),
]

NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_lte_int", expression={"$lte": [FLOAT_NAN, 1]}, expected=True, msg="NaN <= int"
    ),
    ExpressionTestCase(
        "int_lte_nan", expression={"$lte": [1, FLOAT_NAN]}, expected=False, msg="int not <= NaN"
    ),
    ExpressionTestCase(
        "nan_lte_neg_inf",
        expression={"$lte": [FLOAT_NAN, FLOAT_NEGATIVE_INFINITY]},
        expected=True,
        msg="NaN <= -Infinity in BSON order",
    ),
]

ALL_TESTS = INFINITY_TESTS + NAN_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_lte_nan_infinity(collection, test):
    """Test $lte Infinity handling."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
