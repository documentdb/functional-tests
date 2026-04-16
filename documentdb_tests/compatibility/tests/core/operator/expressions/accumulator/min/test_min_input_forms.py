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

# Property [Arity]: $min accepts empty arrays and large operand counts.
MIN_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arity_empty_array",
        expression={"$min": []},
        expected=None,
        msg="$min should return null for an empty array",
    ),
    ExpressionTestCase(
        "arity_large_operand_count",
        expression={"$min": list(range(10_000))},
        expected=0,
        msg="$min should handle 10,000 operands correctly",
    ),
]

# Property [Input Forms]: $min accepts literals, expressions, field paths
# into arrays and objects, and composite array paths.
MIN_INPUT_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "input_literal",
        expression={"$min": ["$a", 10]},
        doc={"a": 3},
        expected=3,
        msg="$min should accept a literal value as an operand",
    ),
    ExpressionTestCase(
        "input_expression",
        expression={"$min": [{"$multiply": ["$a", "$b"]}, "$c"]},
        doc={"a": 3, "b": 2, "c": 1},
        expected=1,
        msg="$min should accept an expression as an operand",
    ),
    ExpressionTestCase(
        "input_array_index",
        expression={"$min": [{"$arrayElemAt": ["$a", 0]}, {"$arrayElemAt": ["$a", 1]}]},
        doc={"a": [7, 9]},
        expected=7,
        msg="$min should accept array element expressions as operands",
    ),
    ExpressionTestCase(
        "input_nested_object",
        expression={"$min": ["$a.x", "$a.y"]},
        doc={"a": {"x": 3, "y": 8}},
        expected=3,
        msg="$min should accept nested object field paths as operands",
    ),
    ExpressionTestCase(
        "input_composite_array",
        expression={"$min": "$a.val"},
        doc={"a": [{"val": 4}, {"val": 9}, {"val": 1}]},
        expected=1,
        msg="$min should traverse a composite array path and return the min",
    ),
]

MIN_INPUT_FORM_AND_ARITY_TESTS = MIN_ARITY_TESTS + MIN_INPUT_FORM_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MIN_INPUT_FORM_AND_ARITY_TESTS))
def test_min_input_form_cases(collection, test_case: ExpressionTestCase):
    """Test $min input form and arity cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
