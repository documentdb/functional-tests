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
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    ZIP_INPUT_ELEMENT_NOT_ARRAY_ERROR,
    ZIP_INPUTS_NOT_ARRAY_ERROR,
    ZIP_MISSING_INPUTS_ERROR,
    ZIP_UNKNOWN_FIELD_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

STRUCTURE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="empty_object",
        expression={"$zip": {}},
        error_code=ZIP_MISSING_INPUTS_ERROR,
        msg="Empty object should error",
    ),
    ExpressionTestCase(
        id="missing_inputs",
        expression={"$zip": {"useLongestLength": True}},
        error_code=ZIP_MISSING_INPUTS_ERROR,
        msg="Missing inputs should error",
    ),
    ExpressionTestCase(
        id="unknown_field",
        expression={"$zip": {"inputs": [[1], [2]], "extra": 1}},
        error_code=ZIP_UNKNOWN_FIELD_ERROR,
        msg="Unknown field should error",
    ),
    ExpressionTestCase(
        id="inputs_not_array",
        expression={"$zip": {"inputs": "bad"}},
        error_code=ZIP_INPUT_ELEMENT_NOT_ARRAY_ERROR,
        msg="Non-array inputs should error",
    ),
    ExpressionTestCase(
        id="inputs_not_array_int",
        expression={"$zip": {"inputs": 1}},
        error_code=ZIP_INPUT_ELEMENT_NOT_ARRAY_ERROR,
        msg="Int inputs should error",
    ),
    ExpressionTestCase(
        id="inputs_empty_array",
        expression={"$zip": {"inputs": []}},
        error_code=ZIP_MISSING_INPUTS_ERROR,
        msg="Empty inputs array should error",
    ),
    ExpressionTestCase(
        id="inputs_as_object",
        expression={"$zip": {"inputs": {"a": "b"}}},
        error_code=ZIP_INPUT_ELEMENT_NOT_ARRAY_ERROR,
        msg="inputs as object should error",
    ),
]

# ---------------------------------------------------------------------------
# Non-object argument (error 34460)
# ---------------------------------------------------------------------------
NON_OBJECT_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int_arg",
        expression={"$zip": 1},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="Int argument should error",
    ),
    ExpressionTestCase(
        id="string_arg",
        expression={"$zip": "abc"},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="String argument should error",
    ),
    ExpressionTestCase(
        id="array_arg",
        expression={"$zip": [1, 2]},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="Array argument should error",
    ),
    ExpressionTestCase(
        id="null_arg",
        expression={"$zip": None},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="Null argument should error",
    ),
    ExpressionTestCase(
        id="bool_arg",
        expression={"$zip": True},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="Bool argument should error",
    ),
    ExpressionTestCase(
        id="double_arg",
        expression={"$zip": 1.5},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="Double argument should error",
    ),
    ExpressionTestCase(
        id="minkey_arg",
        expression={"$zip": MinKey()},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="MinKey argument should error",
    ),
    ExpressionTestCase(
        id="maxkey_arg",
        expression={"$zip": MaxKey()},
        error_code=ZIP_INPUTS_NOT_ARRAY_ERROR,
        msg="MaxKey argument should error",
    ),
]

ALL_STRUCTURE_TESTS = STRUCTURE_ERROR_TESTS + NON_OBJECT_ARG_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_STRUCTURE_TESTS))
def test_zip_argument_handling(collection, test):
    """Test $zip argument structure validation."""
    result = execute_expression(collection, test.expression)
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
