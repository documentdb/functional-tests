"""
Tests for $lte argument handling.

Covers argument count variations and error cases.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import EXPRESSION_TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

LTE_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "no_args",
        expression={"$lte": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for empty arguments",
    ),
    ExpressionTestCase(
        "single_arg",
        expression={"$lte": [1]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for single argument",
    ),
    ExpressionTestCase(
        "non_array_int",
        expression={"$lte": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for non-array int argument",
    ),
    ExpressionTestCase(
        "non_array_string",
        expression={"$lte": "$field"},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for non-array string argument",
    ),
    ExpressionTestCase(
        "three_args",
        expression={"$lte": [1, 2, 3]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for three arguments",
    ),
    ExpressionTestCase(
        "two_args_lt",
        expression={"$lte": [1, 2]},
        expected=True,
        msg="Should return true when first < second",
    ),
    ExpressionTestCase(
        "two_args_eq",
        expression={"$lte": [1, 1]},
        expected=True,
        msg="Should return true when equal",
    ),
    ExpressionTestCase(
        "two_args_gt",
        expression={"$lte": [2, 1]},
        expected=False,
        msg="Should return false when first > second",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LTE_ARG_TESTS))
def test_lte_argument_handling(collection, test):
    """Test $lte argument count variations."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
