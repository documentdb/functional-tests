"""
Tests for $lt Infinity handling.

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
        "1_lt_inf", expression={"$lt": [1, FLOAT_INFINITY]}, expected=True, msg="1 < Inf"
    ),
    ExpressionTestCase(
        "inf_lt_1", expression={"$lt": [FLOAT_INFINITY, 1]}, expected=False, msg="Inf not < 1"
    ),
    ExpressionTestCase(
        "neg_inf_lt_1",
        expression={"$lt": [FLOAT_NEGATIVE_INFINITY, 1]},
        expected=True,
        msg="-Inf < 1",
    ),
    ExpressionTestCase(
        "1_lt_neg_inf",
        expression={"$lt": [1, FLOAT_NEGATIVE_INFINITY]},
        expected=False,
        msg="1 not < -Inf",
    ),
    ExpressionTestCase(
        "neg_inf_lt_inf",
        expression={"$lt": [FLOAT_NEGATIVE_INFINITY, FLOAT_INFINITY]},
        expected=True,
        msg="-Inf < Inf",
    ),
    ExpressionTestCase(
        "inf_lt_neg_inf",
        expression={"$lt": [FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=False,
        msg="Inf not < -Inf",
    ),
    ExpressionTestCase(
        "inf_self",
        expression={"$lt": [FLOAT_INFINITY, FLOAT_INFINITY]},
        expected=False,
        msg="Inf not < Inf",
    ),
    ExpressionTestCase(
        "neg_inf_self",
        expression={"$lt": [FLOAT_NEGATIVE_INFINITY, FLOAT_NEGATIVE_INFINITY]},
        expected=False,
        msg="-Inf not < -Inf",
    ),
    ExpressionTestCase(
        "near_max_lt_inf",
        expression={"$lt": [DOUBLE_NEAR_MAX, FLOAT_INFINITY]},
        expected=True,
        msg="DOUBLE_NEAR_MAX < Inf",
    ),
]


NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_lt_int", expression={"$lt": [FLOAT_NAN, 1]}, expected=True, msg="NaN < int"
    ),
    ExpressionTestCase(
        "int_lt_nan", expression={"$lt": [1, FLOAT_NAN]}, expected=False, msg="int not < NaN"
    ),
    ExpressionTestCase(
        "nan_lt_neg_inf",
        expression={"$lt": [FLOAT_NAN, FLOAT_NEGATIVE_INFINITY]},
        expected=True,
        msg="NaN < -Infinity in BSON order",
    ),
]

ALL_TESTS = INF_TESTS + NAN_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_lt_nan_infinity(collection, test):
    """Test $lt Infinity handling."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
