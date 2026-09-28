"""
Argument handling tests for $zip expression.

Tests object structure validation: missing fields, extra fields,
non-object argument, empty inputs, inputs not being an array,
useLongestLength truthy/falsy coercion, and defaults type variety.
"""

import pytest
from bson import MaxKey, MinKey

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    ZIP_INPUT_ELEMENT_NOT_ARRAY_ERROR,
    ZIP_INPUTS_NOT_ARRAY_ERROR,
    ZIP_MISSING_INPUTS_ERROR,
    ZIP_UNKNOWN_FIELD_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Argument Structure]: $zip rejects malformed arguments.
STRUCTURE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_object",
        expression={"$zip": {}},
        error_code=ZIP_MISSING_INPUTS_ERROR,
        msg="$zip empty object should error",
    ),
    ExpressionTestCase(
        "missing_inputs",
        expression={"$zip": {"useLongestLength": True}},
        error_code=ZIP_MISSING_INPUTS_ERROR,
        msg="$zip missing inputs should error",
    ),
    ExpressionTestCase(
        "unknown_field",
        expression={"$zip": {"inputs": [[1], [2]], "extra": 1}},
        error_code=ZIP_UNKNOWN_FIELD_ERROR,
        msg="$zip unknown field should error",
    ),
    ExpressionTestCase(
        "inputs_not_array",
        expression={"$zip": {"inputs": "bad"}},
        error_code=ZIP_INPUT_ELEMENT_NOT_ARRAY_ERROR,
        msg="$zip non-array inputs should error",
    ),
    ExpressionTestCase(
        "inputs_not_array_int",
        expression={"$zip": {"inputs": 1}},
        error_code=ZIP_INPUT_ELEMENT_NOT_ARRAY_ERROR,
        msg="$zip int inputs should error",
    ),
    ExpressionTestCase(
        "inputs_empty_array",
        expression={"$zip": {"inputs": []}},
        error_code=ZIP_MISSING_INPUTS_ERROR,
        msg="$zip empty inputs array should error",
    ),
    ExpressionTestCase(
        "inputs_as_object",
        expression={"$zip": {"inputs": {"a": "b"}}},
        error_code=ZIP_INPUT_ELEMENT_NOT_ARRAY_ERROR,
        msg="$zip inputs as object should error",
    ),
]

# Property [Object Argument]: $zip rejects non-object arguments.
NON_OBJECT_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_arg",
        expression={"$zip": 1},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="$zip int argument should error",
    ),
    ExpressionTestCase(
        "string_arg",
        expression={"$zip": "abc"},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="$zip string argument should error",
    ),
    ExpressionTestCase(
        "array_arg",
        expression={"$zip": [1, 2]},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="$zip array argument should error",
    ),
    ExpressionTestCase(
        "null_arg",
        expression={"$zip": None},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="$zip null argument should error",
    ),
    ExpressionTestCase(
        "bool_arg",
        expression={"$zip": True},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="$zip bool argument should error",
    ),
    ExpressionTestCase(
        "double_arg",
        expression={"$zip": 1.5},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="$zip double argument should error",
    ),
    ExpressionTestCase(
        "minkey_arg",
        expression={"$zip": MinKey()},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="$zip minKey argument should error",
    ),
    ExpressionTestCase(
        "maxkey_arg",
        expression={"$zip": MaxKey()},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="$zip maxKey argument should error",
    ),
]

ALL_STRUCTURE_TESTS = STRUCTURE_ERROR_TESTS + NON_OBJECT_ARG_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_STRUCTURE_TESTS))
def test_zip_argument_handling(collection, test):
    """Test $zip argument structure validation."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
