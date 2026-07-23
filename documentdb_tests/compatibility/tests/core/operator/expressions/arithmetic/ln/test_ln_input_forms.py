"""Tests for $ln argument forms, literal input, and nested expression input."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_ZERO

# Property [Argument Form]: $ln accepts its single argument bare or wrapped in a one-element array.
LN_ARGUMENT_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "form_array",
        doc={"value": 1},
        expression={"$ln": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$ln should accept its argument wrapped in a one-element array",
    ),
    ExpressionTestCase(
        "form_bare",
        doc={"value": 1},
        expression={"$ln": "$value"},
        expected=DOUBLE_ZERO,
        msg="$ln should accept its argument without an array wrapper",
    ),
]

# Property [Literal Input]: $ln evaluates an inline literal argument, not only document fields.
LN_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_input",
        doc={},
        expression={"$ln": [1]},
        expected=DOUBLE_ZERO,
        msg="$ln should return zero for an inline literal one",
    ),
]

# Property [Expression Input]: $ln evaluates a nested expression argument before taking the log.
LN_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_exp",
        doc={},
        expression={"$ln": {"$exp": 1}},
        expected=pytest.approx(1.0),
        msg="$ln should evaluate a nested $exp expression argument",
    ),
]

LN_INPUT_FORM_TESTS = LN_ARGUMENT_FORM_TESTS + LN_LITERAL_TESTS + LN_EXPRESSION_INPUT_TESTS


@pytest.mark.parametrize("test_case", pytest_params(LN_INPUT_FORM_TESTS))
def test_ln_input_forms(collection, test_case: ExpressionTestCase):
    """Test $ln argument form, literal, and nested expression input cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
