from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Input Form Handling]: $sum accepts single values, arrays,
# field references, and nested expressions as input.
SUM_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arity_empty",
        expression={"$sum": []},
        expected=0,
        msg="$sum of empty array should return 0",
    ),
    ExpressionTestCase(
        "arity_single",
        expression={"$sum": "$a"},
        doc={"a": 7},
        expected=7,
        msg="$sum of a single operand should return that operand",
    ),
    ExpressionTestCase(
        "arity_large",
        expression={"$sum": ["$a"] * 10_000},
        doc={"a": 1},
        expected=10_000,
        msg="$sum should handle 10,000 operands correctly",
    ),
]

# Property [Input Forms]: $sum accepts field paths, literal values, and expression operands.
SUM_INPUT_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "input_literal",
        expression={"$sum": ["$a", 10]},
        doc={"a": 3},
        expected=13,
        msg="$sum should accept a literal value as an operand",
    ),
    ExpressionTestCase(
        "input_array_field_traversal",
        expression={"$sum": "$arr"},
        doc={"arr": [1, 2, 3]},
        expected=6,
        msg="$sum should traverse array field reference in single expression form",
    ),
    ExpressionTestCase(
        "input_nested_object",
        expression={"$sum": ["$a.x", "$a.y"]},
        doc={"a": {"x": 3, "y": 7}},
        expected=10,
        msg="$sum should accept nested object field paths",
    ),
    ExpressionTestCase(
        "input_composite_array",
        expression={"$sum": "$a.val"},
        doc={"a": [{"val": 4}, {"val": 9}, {"val": 1}]},
        expected=14,
        msg="$sum should traverse a composite array path and sum values",
    ),
    ExpressionTestCase(
        "input_expression_operand",
        expression={"$sum": [{"$multiply": ["$a", "$b"]}, "$c"]},
        doc={"a": 3, "b": 2, "c": 4},
        expected=10,
        msg="$sum should accept an expression as an operand",
    ),
]

SUM_INPUT_ALL_TESTS = SUM_ARITY_TESTS + SUM_INPUT_FORM_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SUM_INPUT_ALL_TESTS))
def test_sum_input_forms(collection, test_case: ExpressionTestCase):
    """Test $sum arity and input forms."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
