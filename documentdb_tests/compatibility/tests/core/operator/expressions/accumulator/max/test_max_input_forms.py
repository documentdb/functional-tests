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

# Property [Arity]: $max accepts empty arrays and large operand counts.
MAX_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arity_empty_array",
        expression={"$max": []},
        expected=None,
        msg="$max should return null for an empty array",
    ),
    ExpressionTestCase(
        "arity_large_operand_count",
        expression={"$max": list(range(10_000))},
        expected=9_999,
        msg="$max should handle 10,000 operands correctly",
    ),
]

# Property [Input Forms]: $max accepts literals, expressions, field paths
# into arrays and objects, and composite array paths.
MAX_INPUT_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "input_literal",
        expression={"$max": ["$a", 10]},
        doc={"a": 3},
        expected=10,
        msg="$max should accept a literal value as an operand",
    ),
    ExpressionTestCase(
        "input_expression",
        expression={"$max": [{"$multiply": ["$a", "$b"]}, "$c"]},
        doc={"a": 3, "b": 2, "c": 1},
        expected=6,
        msg="$max should accept an expression as an operand",
    ),
    ExpressionTestCase(
        "input_array_index",
        expression={"$max": [{"$arrayElemAt": ["$a", 0]}, {"$arrayElemAt": ["$a", 1]}]},
        doc={"a": [7, 9]},
        expected=9,
        msg="$max should accept array element expressions as operands",
    ),
    ExpressionTestCase(
        "input_nested_object",
        expression={"$max": ["$a.x", "$a.y"]},
        doc={"a": {"x": 3, "y": 8}},
        expected=8,
        msg="$max should accept nested object field paths as operands",
    ),
    ExpressionTestCase(
        "input_composite_array",
        expression={"$max": "$a.val"},
        doc={"a": [{"val": 4}, {"val": 9}, {"val": 1}]},
        expected=9,
        msg="$max should traverse a composite array path and return the max",
    ),
]

MAX_INPUT_FORM_AND_ARITY_TESTS = MAX_ARITY_TESTS + MAX_INPUT_FORM_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MAX_INPUT_FORM_AND_ARITY_TESTS))
def test_max_input_form_cases(collection, test_case: ExpressionTestCase):
    """Test $max input form and arity cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
