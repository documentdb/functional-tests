from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params

from ...utils.expression_test_case import ExpressionTestCase
from .utils.trim_common import (
    TrimTest,
    _expr,
)

# Property [Expression Arguments]: input and chars accept any expression that resolves to a
# string. Nested $trim expressions are also accepted.
TRIM_EXPR_TESTS: list[TrimTest] = [
    # input is an expression.
    TrimTest(
        "expr_input_concat",
        input={"$concat": ["  ", "hello", "  "]},
        expected="hello",
        msg="$trim should accept $concat expression as input",
    ),
    # chars is an expression.
    TrimTest(
        "expr_chars_concat",
        input="aaahelloaaa",
        chars={"$concat": ["a"]},
        expected="hello",
        msg="$trim should accept $concat expression as chars",
    ),
    # Both input and chars are expressions.
    TrimTest(
        "expr_both",
        input={"$concat": ["xx", "hello", "xx"]},
        chars={"$concat": ["x"]},
        expected="hello",
        msg="$trim should accept expressions for both input and chars",
    ),
    # Nested $trim as input to another $trim.
    TrimTest(
        "expr_nested_trim",
        input={"$trim": {"input": "  aahelloaa  "}},
        chars="a",
        expected="hello",
        msg="$trim should accept nested $trim as input expression",
    ),
    # $literal for dollar-prefixed strings.
    TrimTest(
        "expr_literal_dollar",
        input={"$literal": "$$$hello$$$"},
        chars={"$literal": "$"},
        expected="hello",
        msg="$trim should accept $literal for dollar-prefixed strings",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TRIM_EXPR_TESTS))
def test_trim_input_forms(collection, test_case: TrimTest):
    """Test $trim input forms."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


# Property [Document Field References]: $trim works with field references
# from inserted documents, not just inline literals.
TRIM_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    # Object expression: both input and chars from simple field paths.
    ExpressionTestCase(
        "field_object",
        expression={"$trim": {"input": "$s", "chars": "$c"}},
        doc={"s": "aaahelloaaa", "c": "a"},
        expected="hello",
        msg="$trim should accept input and chars from document field paths",
    ),
    # Composite array: both from $arrayElemAt on a projected array-of-objects field.
    ExpressionTestCase(
        "field_composite_array",
        expression={
            "$trim": {
                "input": {"$arrayElemAt": ["$a.b", 0]},
                "chars": {"$arrayElemAt": ["$a.b", 1]},
            }
        },
        doc={"a": [{"b": "aaahelloaaa"}, {"b": "a"}]},
        expected="hello",
        msg="$trim should accept input and chars from composite array field paths",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TRIM_FIELD_REF_TESTS))
def test_trim_field_refs(collection, test_case: ExpressionTestCase):
    """Test $trim with document field references."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
