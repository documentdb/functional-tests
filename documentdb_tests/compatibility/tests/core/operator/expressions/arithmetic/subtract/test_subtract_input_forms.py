"""Input form and field path tests for the $subtract operator."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import EXPRESSION_TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Literal Input]: $subtract evaluates inline literal arguments.
# Property [Expression Input]: $subtract evaluates nested expressions.
# Property [Field Path]: $subtract resolves field paths from documents.
SUBTRACT_INPUT_FORM_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_operands",
        doc={},
        expression={"$subtract": [10, 3]},
        expected=7,
        msg="Should subtract literal values",
    ),
    ExpressionTestCase(
        "nested_subtract_2",
        doc={},
        expression={"$subtract": [{"$subtract": [10, 3]}, 2]},
        expected=5,
        msg="Should subtract nested expression results",
    ),
    ExpressionTestCase(
        "nested_subtract_3",
        doc={},
        expression={"$subtract": [{"$subtract": [{"$subtract": [100, 10]}, 20]}, 30]},
        expected=40,
        msg="Should subtract deeply nested expression results",
    ),
    ExpressionTestCase(
        "nested_field",
        doc={"a": {"b": 10}, "c": 3},
        expression={"$subtract": ["$a.b", "$c"]},
        expected=7,
        msg="Should subtract resolved nested field values",
    ),
    ExpressionTestCase(
        "nonexistent_field",
        doc={"a": {"missing": 1}, "b": 5},
        expression={"$subtract": ["$a.nonexistent", "$b"]},
        expected=None,
        msg="Should return null when a field path does not exist",
    ),
    ExpressionTestCase(
        "array_index",
        doc={"arr": [10, 5, 2]},
        expression={
            "$subtract": [
                {"$arrayElemAt": ["$arr", 0]},
                {"$arrayElemAt": ["$arr", 1]},
            ]
        },
        expected=5,
        msg="Should subtract values accessed via array index expressions",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        doc={"a": {"b": {"c": {"d": 20}}}},
        expression={"$subtract": ["$a.b.c.d", 8]},
        expected=12,
        msg="Should subtract a deeply nested field value",
    ),
    ExpressionTestCase(
        "composite_array_field",
        doc={"x": [{"y": 10}, {"y": 3}]},
        expression={"$subtract": "$x.y"},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject composite array from field path",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_INPUT_FORM_TESTS))
def test_subtract_input_forms(collection, test_case: ExpressionTestCase):
    """Test $subtract input form and field path cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
