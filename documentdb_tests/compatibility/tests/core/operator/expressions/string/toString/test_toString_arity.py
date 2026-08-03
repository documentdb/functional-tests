"""$toString arity and field path syntax tests."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

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
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [Arity]: $toString unwraps single-element literal arrays and rejects empty or
# multi-element arrays. Non-convertible types unwrapped from a single-element array are
# rejected with a conversion failure.
TOSTRING_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_null",
        msg="Single-element literal array wrapping null unwraps and returns null",
        expression={"$toString": [None]},
        expected=None,
    ),
    ExpressionTestCase(
        "single_bool",
        msg="Single-element literal array wrapping bool unwraps and converts",
        expression={"$toString": [True]},
        expected="true",
    ),
    ExpressionTestCase(
        "single_int32",
        msg="Single-element literal array wrapping int32 unwraps and converts",
        expression={"$toString": [42]},
        expected="42",
    ),
    ExpressionTestCase(
        "single_int64",
        msg="Single-element literal array wrapping int64 unwraps and converts",
        expression={"$toString": [Int64(99)]},
        expected="99",
    ),
    ExpressionTestCase(
        "single_double",
        msg="Single-element literal array wrapping double unwraps and converts",
        expression={"$toString": [3.14]},
        expected="3.14",
    ),
    ExpressionTestCase(
        "single_decimal128",
        msg="Single-element literal array wrapping Decimal128 unwraps and converts",
        expression={"$toString": [DECIMAL128_ONE_AND_HALF]},
        expected="1.5",
    ),
    ExpressionTestCase(
        "single_string",
        msg="Single-element literal array wrapping string unwraps and returns it",
        expression={"$toString": ["hello"]},
        expected="hello",
    ),
    ExpressionTestCase(
        "single_objectid",
        msg="Single-element literal array wrapping ObjectId unwraps and converts",
        expression={"$toString": [ObjectId("507f1f77bcf86cd799439011")]},
        expected="507f1f77bcf86cd799439011",
    ),
    ExpressionTestCase(
        "single_datetime",
        msg="Single-element literal array wrapping datetime unwraps and converts",
        expression={"$toString": [datetime(2024, 1, 1, tzinfo=timezone.utc)]},
        expected="2024-01-01T00:00:00.000Z",
    ),
    ExpressionTestCase(
        "single_binary",
        msg="Single-element literal array wrapping Binary unwraps and converts",
        expression={"$toString": [Binary(b"hi", 0)]},
        expected="aGk=",
    ),
    ExpressionTestCase(
        "single_minkey",
        msg="Single-element array with MinKey unwraps then rejects with conversion failure",
        expression={"$toString": [MinKey()]},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "single_maxkey",
        msg="Single-element array with MaxKey unwraps then rejects with conversion failure",
        expression={"$toString": [MaxKey()]},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "single_timestamp",
        msg="Single-element array with Timestamp unwraps then rejects with conversion failure",
        expression={"$toString": [Timestamp(1, 1)]},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "single_regex",
        msg="Single-element array with Regex unwraps then rejects with conversion failure",
        expression={"$toString": [Regex("abc")]},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "single_code",
        msg="Single-element array with Code unwraps then rejects with conversion failure",
        expression={"$toString": [Code("x")]},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "empty_array",
        msg="Empty literal array is an arity error",
        expression={"$toString": []},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "two_elements",
        msg="Two-element literal array is an arity error",
        expression={"$toString": ["a", "b"]},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
    ExpressionTestCase(
        "large_array",
        msg="Large literal array is an arity error",
        expression={"$toString": list(range(100))},
        error_code=TO_TYPE_ARITY_ERROR,
    ),
]

# Property [Invalid Field Path]: $toString rejects malformed field path syntax.
TOSTRING_INVALID_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bare_dollar",
        msg="Bare '$' is an invalid field path",
        expression={"$toString": "$"},
        error_code=INVALID_DOLLAR_FIELD_PATH,
    ),
    ExpressionTestCase(
        "double_dollar",
        msg="'$$' is rejected as an empty variable name",
        expression={"$toString": "$$"},
        error_code=FAILED_TO_PARSE_ERROR,
    ),
]


@pytest.mark.parametrize(
    "test", pytest_params(TOSTRING_ARITY_TESTS + TOSTRING_INVALID_FIELD_PATH_TESTS)
)
def test_toString_arity(collection, test: ExpressionTestCase):
    """$toString literal array arguments are unwrapped or rejected based on arity."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
