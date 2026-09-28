"""Tests for $abs argument forms, literals, field paths, and nested expression inputs."""

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

# Property [Argument Form]: $abs accepts its single argument bare or wrapped in a one-element
# array.
ABS_ARGUMENT_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "form_array",
        doc={"value": -5},
        expression={"$abs": ["$value"]},
        expected=5,
        msg="$abs should accept its argument wrapped in a one-element array",
    ),
    ExpressionTestCase(
        "form_bare",
        doc={"value": -5},
        expression={"$abs": "$value"},
        expected=5,
        msg="$abs should accept its argument without an array wrapper",
    ),
]

# Property [Literal Input]: $abs evaluates an inline literal argument, not only document fields.
ABS_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_input",
        doc={},
        expression={"$abs": [-5]},
        expected=5,
        msg="$abs should return the absolute value of an inline literal argument",
    ),
]

# Property [Expression Input]: $abs evaluates a nested expression argument before taking the
# absolute value.
ABS_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_abs",
        doc={"value": -4},
        expression={"$abs": {"$abs": "$value"}},
        expected=4,
        msg="$abs should evaluate a nested $abs expression argument",
    ),
]

# Property [Field Path Input]: $abs resolves a field path argument. A dotted path into a nested
# object yields the referenced value; a path over an array of objects resolves to an array, which
# $abs rejects as a non-numeric type.
ABS_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field_path",
        doc={"a": {"b": -5}},
        expression={"$abs": "$a.b"},
        expected=5,
        msg="$abs should resolve a dotted field path into a nested object",
    ),
    ExpressionTestCase(
        "composite_array_field_path",
        doc={"a": [{"b": -1}, {"b": -2}]},
        expression={"$abs": "$a.b"},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="$abs should reject a field path that resolves to an array from an array of objects",
    ),
    ExpressionTestCase(
        "array_index_field_path",
        doc={"a": [-5, -6]},
        expression={"$abs": "$a.0"},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="$abs should reject a numeric path component over an array, which resolves non-numeric",
    ),
]

ABS_INPUT_FORM_TESTS = (
    ABS_ARGUMENT_FORM_TESTS + ABS_LITERAL_TESTS + ABS_EXPRESSION_INPUT_TESTS + ABS_FIELD_PATH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ABS_INPUT_FORM_TESTS))
def test_abs_input_forms(collection, test_case: ExpressionTestCase):
    """Test $abs argument form, literal, field path, and nested expression input cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
