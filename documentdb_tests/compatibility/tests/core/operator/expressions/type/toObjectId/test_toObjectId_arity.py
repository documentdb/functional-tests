"""$toObjectId arity and field path syntax tests."""

import pytest
from bson import ObjectId

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    TO_TYPE_ARITY_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Arity]: $toObjectId unwraps single-element literal arrays and rejects empty or
# multi-element arrays. These cases are specific to $toObjectId syntax (not $convert).
TOOBJECTID_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_element_string",
        msg="Single-element literal array containing a valid hex string is unwrapped and converts",
        expression={"$toObjectId": ["507f1f77bcf86cd799439011"]},
        expected=ObjectId("507f1f77bcf86cd799439011"),
    ),
    ExpressionTestCase(
        "single_null",
        msg="Single-element literal array wrapping null unwraps and returns null",
        expression={"$toObjectId": [None]},
        expected=None,
    ),
    ExpressionTestCase(
        "empty_array",
        msg="Empty literal array argument is an arity error",
        expression={"$toObjectId": []},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "multi_element",
        msg="Multi-element literal array argument is an arity error",
        expression={"$toObjectId": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439011"]},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "large_array",
        msg="A large literal array argument is an arity error",
        expression={"$toObjectId": ["0" * 24] * 10},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "single_invalid_type",
        msg="Single-element array wrapping an int unwraps, then fails as invalid type",
        expression={"$toObjectId": [42]},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "single_nested_array",
        msg="Single-element array wrapping another array unwraps one level, then fails",
        expression={"$toObjectId": [["507f1f77bcf86cd799439011"]]},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

# Property [Invalid Field Path]: $toObjectId rejects malformed field path syntax.
TOOBJECTID_INVALID_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bare_dollar",
        msg="Bare '$' is an invalid field path",
        expression={"$toObjectId": "$"},
        error_code=INVALID_DOLLAR_FIELD_PATH,
    ),
    ExpressionTestCase(
        "double_dollar",
        msg="'$$' is rejected as an empty variable name",
        expression={"$toObjectId": "$$"},
        error_code=FAILED_TO_PARSE_ERROR,
    ),
]

TOOBJECTID_ARITY_AND_PATH_TESTS = TOOBJECTID_ARITY_TESTS + TOOBJECTID_INVALID_FIELD_PATH_TESTS


@pytest.mark.parametrize("test", pytest_params(TOOBJECTID_ARITY_AND_PATH_TESTS))
def test_toObjectId_arity(collection, test: ExpressionTestCase):
    """$toObjectId literal array arguments are unwrapped or rejected based on arity."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
