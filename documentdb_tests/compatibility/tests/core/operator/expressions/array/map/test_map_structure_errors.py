"""
Structural error tests for $map expression.

Tests invalid $map argument structure: non-object argument, unknown/misspelled fields,
missing required fields (input, in), and runtime errors in the 'in' expression.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_NON_OBJECT_ARG_ERROR,
    MAP_MISSING_IN_ERROR,
    MAP_MISSING_INPUT_ERROR,
    MAP_UNKNOWN_FIELD_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Object Argument]: $map rejects non-object arguments.
NON_OBJECT_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_arg",
        expression={"$map": None},
        error_code=EXPRESSION_NON_OBJECT_ARG_ERROR,
        msg="$map null arg should error",
    ),
    ExpressionTestCase(
        "int_arg",
        expression={"$map": 1},
        error_code=EXPRESSION_NON_OBJECT_ARG_ERROR,
        msg="$map int arg should error",
    ),
    ExpressionTestCase(
        "string_arg",
        expression={"$map": "string"},
        error_code=EXPRESSION_NON_OBJECT_ARG_ERROR,
        msg="$map string arg should error",
    ),
    ExpressionTestCase(
        "array_arg",
        expression={"$map": [1, 2]},
        error_code=EXPRESSION_NON_OBJECT_ARG_ERROR,
        msg="$map array arg should error",
    ),
    ExpressionTestCase(
        "bool_arg",
        expression={"$map": True},
        error_code=EXPRESSION_NON_OBJECT_ARG_ERROR,
        msg="$map bool arg should error",
    ),
]

# Property [Unknown Fields]: $map rejects unknown fields in the argument.
UNKNOWN_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "extra_unknown",
        expression={"$map": {"input": [1], "in": "$$this", "unknown": 1}},
        error_code=MAP_UNKNOWN_FIELD_ERROR,
        msg="$map extra unknown field should error",
    ),
    ExpressionTestCase(
        "misspelled_inputs",
        expression={"$map": {"inputs": [1], "in": "$$this"}},
        error_code=MAP_UNKNOWN_FIELD_ERROR,
        msg="$map misspelled 'inputs' should error",
    ),
]

# Property [Required Fields]: $map requires the input and in fields.
MISSING_REQUIRED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_input",
        expression={"$map": {"in": "$$this"}},
        error_code=MAP_MISSING_INPUT_ERROR,
        msg="$map missing input should error",
    ),
    ExpressionTestCase(
        "missing_in",
        expression={"$map": {"input": [1, 2, 3]}},
        error_code=MAP_MISSING_IN_ERROR,
        msg="$map missing in should error",
    ),
    ExpressionTestCase(
        "missing_in_with_as",
        expression={"$map": {"input": [1, 2, 3], "as": "x"}},
        error_code=MAP_MISSING_IN_ERROR,
        msg="$map missing in with as should error",
    ),
    ExpressionTestCase(
        "empty_object",
        expression={"$map": {}},
        error_code=MAP_MISSING_INPUT_ERROR,
        msg="$map empty object should error",
    ),
]

ALL_STRUCTURE_TESTS = NON_OBJECT_ARG_TESTS + UNKNOWN_FIELD_TESTS + MISSING_REQUIRED_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_STRUCTURE_TESTS))
def test_map_structure_error(collection, test):
    """Test $map argument structure validation."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
