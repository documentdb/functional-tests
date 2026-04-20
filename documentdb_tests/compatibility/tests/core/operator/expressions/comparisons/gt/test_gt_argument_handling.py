"""
Tests for $gt argument handling.

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

GT_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "no_args",
        expression={"$gt": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for empty arguments",
    ),
    ExpressionTestCase(
        "single_arg",
        expression={"$gt": [1]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for single argument",
    ),
    ExpressionTestCase(
        "non_array_arg",
        expression={"$gt": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for non-array argument",
    ),
    ExpressionTestCase(
        "non_array_string",
        expression={"$gt": "string"},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for string argument",
    ),
    ExpressionTestCase(
        "three_args",
        expression={"$gt": [3, 2, 1]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for three arguments",
    ),
    ExpressionTestCase(
        "two_args_gt",
        expression={"$gt": [2, 1]},
        expected=True,
        msg="Should return true when first > second",
    ),
    ExpressionTestCase(
        "two_args_eq",
        expression={"$gt": [1, 1]},
        expected=False,
        msg="Should return false when equal",
    ),
    ExpressionTestCase(
        "two_args_lt",
        expression={"$gt": [1, 2]},
        expected=False,
        msg="Should return false when first < second",
    ),
]


@pytest.mark.parametrize("test", pytest_params(GT_ARG_TESTS))
def test_gt_argument_handling(collection, test):
    """Test $gt argument count variations."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
