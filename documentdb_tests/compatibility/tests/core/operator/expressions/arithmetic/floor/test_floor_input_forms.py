"""Tests for $floor argument forms, literals, field paths, and nested expression inputs."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import NON_NUMERIC_TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Argument Form]: $floor accepts its single argument bare or wrapped in a one-element
# array.
FLOOR_ARGUMENT_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "form_array",
        doc={"value": -1.5},
        expression={"$floor": ["$value"]},
        expected=-2.0,
        msg="$floor should accept its argument wrapped in a one-element array",
    ),
    ExpressionTestCase(
        "form_bare",
        doc={"value": -1.5},
        expression={"$floor": "$value"},
        expected=-2.0,
        msg="$floor should accept its argument without an array wrapper",
    ),
]

# Property [Literal Input]: $floor evaluates an inline literal argument, not only document fields.
FLOOR_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_input",
        doc={},
        expression={"$floor": [1.5]},
        expected=1.0,
        msg="$floor should round down an inline literal argument",
    ),
]

# Property [Expression Input]: $floor evaluates a nested expression argument before flooring.
FLOOR_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_expression",
        doc={},
        expression={"$floor": {"$floor": -4.1}},
        expected=-5.0,
        msg="$floor should evaluate a nested $floor expression argument",
    ),
]

# Property [Field Path Input]: $floor resolves a field path argument. A dotted path into a nested
# object yields the referenced value; a path over an array (an array-of-objects path, or a numeric
# component applied over an array) resolves to an array, which $floor rejects as a non-numeric type.
FLOOR_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field_path",
        doc={"a": {"b": -1.5}},
        expression={"$floor": "$a.b"},
        expected=-2.0,
        msg="$floor should resolve a dotted field path into a nested object",
    ),
    ExpressionTestCase(
        "composite_array_field_path",
        doc={"a": [{"b": -1.5}, {"b": -2.5}]},
        expression={"$floor": "$a.b"},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="$floor should reject a field path that resolves to an array from an array of objects",
    ),
    ExpressionTestCase(
        "array_index_field_path",
        doc={"a": [-1.5, -2.5]},
        expression={"$floor": "$a.0"},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="$floor should reject a numeric path component over an array, resolving non-numeric",
    ),
]

FLOOR_INPUT_FORM_TESTS = (
    FLOOR_ARGUMENT_FORM_TESTS
    + FLOOR_LITERAL_TESTS
    + FLOOR_EXPRESSION_INPUT_TESTS
    + FLOOR_FIELD_PATH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(FLOOR_INPUT_FORM_TESTS))
def test_floor_input_forms(collection, test_case: ExpressionTestCase):
    """Test $floor argument form, literal, field path, and nested expression input cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
