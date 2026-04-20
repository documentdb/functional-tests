"""
Tests for $lt argument handling.

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

LT_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "no_args",
        expression={"$lt": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for empty arguments",
    ),
    ExpressionTestCase(
        "single_arg",
        expression={"$lt": [1]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for single argument",
    ),
    ExpressionTestCase(
        "non_array_arg",
        expression={"$lt": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for non-array argument",
    ),
    ExpressionTestCase(
        "non_array_string",
        expression={"$lt": "string"},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for string argument",
    ),
    ExpressionTestCase(
        "non_array_field_ref",
        expression={"$lt": "$field"},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for non-array field reference argument",
    ),
    ExpressionTestCase(
        "three_args",
        expression={"$lt": [1, 2, 3]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for three arguments",
    ),
    ExpressionTestCase(
        "two_args_lt",
        expression={"$lt": [1, 2]},
        expected=True,
        msg="Should return true when first < second",
    ),
    ExpressionTestCase(
        "two_args_eq",
        expression={"$lt": [1, 1]},
        expected=False,
        msg="Should return false when equal",
    ),
    ExpressionTestCase(
        "two_args_gt",
        expression={"$lt": [2, 1]},
        expected=False,
        msg="Should return false when first > second",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LT_ARG_TESTS))
def test_lt_argument_handling(collection, test):
    """Test $lt argument count variations."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
