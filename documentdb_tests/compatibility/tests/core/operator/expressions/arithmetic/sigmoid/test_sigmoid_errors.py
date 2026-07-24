"""
arithmetic $sigmoid tests.

Error-case tests for the arithmetic $sigmoid operator: non-numeric literal
and inserted values (empty object/array, multi-element array) and composite
array field-path rejection.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Non-numeric and arity-invalid inputs surface the generic TYPE_MISMATCH_ERROR
# (14) rather than the dedicated type/arity codes used by $sqrt/$round.
SIGMOID_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_object",
        expression={"$sigmoid": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty object in literal",
    ),
    ExpressionTestCase(
        "empty_array",
        expression={"$sigmoid": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty array in literal",
    ),
    ExpressionTestCase(
        "single_element_array",
        expression={"$sigmoid": [1]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject single-element array (not treated as unary form)",
    ),
    ExpressionTestCase(
        "array_value",
        expression={"$sigmoid": [1, 2]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject multi-element array value in literal",
    ),
]


SIGMOID_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_object",
        expression={"$sigmoid": "$value"},
        doc={"value": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty object in insert",
    ),
    ExpressionTestCase(
        "empty_array",
        expression={"$sigmoid": "$value"},
        doc={"value": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty array in insert",
    ),
    ExpressionTestCase(
        "single_element_array",
        expression={"$sigmoid": "$value"},
        doc={"value": [1]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject single-element array in insert (not treated as unary form)",
    ),
    ExpressionTestCase(
        "composite_array_field",
        expression={"$sigmoid": "$x.y"},
        doc={"x": [{"y": 1}, {"y": 2}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject composite array from $x.y on array-of-objects",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SIGMOID_LITERAL_TESTS))
def test_sigmoid_literal(collection, test):
    """Test $sigmoid with literal values"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(SIGMOID_INSERT_TESTS))
def test_sigmoid_insert(collection, test):
    """Test $sigmoid with inserted document values"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
