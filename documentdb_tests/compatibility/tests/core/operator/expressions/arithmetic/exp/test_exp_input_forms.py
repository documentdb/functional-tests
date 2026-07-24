"""Tests for $exp argument forms, literal input, field paths, and nested expression input."""

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

# Property [Argument Form]: $exp accepts its single argument bare or wrapped in a one-element
# array.
EXP_ARGUMENT_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "form_array",
        doc={"value": 1},
        expression={"$exp": ["$value"]},
        expected=pytest.approx(2.718281828459045),
        msg="$exp should accept its argument wrapped in a one-element array",
    ),
    ExpressionTestCase(
        "form_bare",
        doc={"value": 1},
        expression={"$exp": "$value"},
        expected=pytest.approx(2.718281828459045),
        msg="$exp should accept its argument without an array wrapper",
    ),
]

# Property [Literal Input]: $exp evaluates an inline literal argument, not only document fields.
EXP_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_input",
        doc={},
        expression={"$exp": [1]},
        expected=pytest.approx(2.718281828459045),
        msg="$exp should return e for an inline literal argument",
    ),
]

# Property [Expression Input]: $exp evaluates a nested expression argument before exponentiating.
EXP_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_exp",
        doc={},
        expression={"$exp": {"$exp": 1}},
        expected=pytest.approx(15.154262241479262),
        msg="$exp should evaluate a nested $exp expression argument",
    ),
]

# Property [Field Path Input]: $exp resolves a field path argument. A dotted path into a nested
# object yields the referenced value; a path over an array (an array-of-objects path, or a numeric
# component applied over an array) resolves to an array, which $exp rejects as a non-numeric type.
EXP_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field_path",
        doc={"a": {"b": 1}},
        expression={"$exp": "$a.b"},
        expected=pytest.approx(2.718281828459045),
        msg="$exp should resolve a dotted field path into a nested object",
    ),
    ExpressionTestCase(
        "composite_array_field_path",
        doc={"a": [{"b": 1}, {"b": 2}]},
        expression={"$exp": "$a.b"},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="$exp should reject a field path that resolves to an array from an array of objects",
    ),
    ExpressionTestCase(
        "array_index_field_path",
        doc={"a": [1, 2]},
        expression={"$exp": "$a.0"},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="$exp should reject a numeric path component over an array, which resolves non-numeric",
    ),
]

EXP_INPUT_FORM_TESTS = (
    EXP_ARGUMENT_FORM_TESTS + EXP_LITERAL_TESTS + EXP_EXPRESSION_INPUT_TESTS + EXP_FIELD_PATH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(EXP_INPUT_FORM_TESTS))
def test_exp_input_forms(collection, test_case: ExpressionTestCase):
    """Test $exp argument form, literal, field path, and nested expression input cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
