from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.ltrim.utils.ltrim_common import (
    LtrimTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import ExpressionTestCase
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_expression_with_insert,
)

# Property [Expression Arguments]: input and chars accept any expression that resolves to a
# string. Nested $ltrim expressions are also accepted.
LTRIM_EXPR_TESTS: list[LtrimTest] = [
    # input is an expression.
    LtrimTest(
        "expr_input_concat",
        input={"$concat": ["  ", "hello"]},
        expected="hello",
        msg="$ltrim should accept $concat expression as input",
    ),
    # chars is an expression.
    LtrimTest(
        "expr_chars_concat",
        input="aaahello",
        chars={"$concat": ["a"]},
        expected="hello",
        msg="$ltrim should accept $concat expression as chars",
    ),
    # Both input and chars are expressions.
    LtrimTest(
        "expr_both",
        input={"$concat": ["xx", "hello"]},
        chars={"$concat": ["x"]},
        expected="hello",
        msg="$ltrim should accept expressions for both input and chars",
    ),
    # Nested $ltrim as input to another $ltrim.
    LtrimTest(
        "expr_nested_ltrim",
        input={"$ltrim": {"input": "  aahello"}},
        chars="a",
        expected="hello",
        msg="$ltrim should accept nested $ltrim as input expression",
    ),
    # $literal for dollar-prefixed strings.
    LtrimTest(
        "expr_literal_dollar",
        input={"$literal": "$$$hello"},
        chars={"$literal": "$"},
        expected="hello",
        msg="$ltrim should accept $literal for dollar-prefixed strings",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LTRIM_EXPR_TESTS))
def test_ltrim_input_forms(collection, test_case: LtrimTest):
    """Test $ltrim expression argument cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


# Property [Document Field References]: $ltrim works with field references
# from inserted documents, not just inline literals.
LTRIM_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    # Object expression: both input and chars from simple field paths.
    ExpressionTestCase(
        "field_object",
        expression={"$ltrim": {"input": "$s", "chars": "$c"}},
        doc={"s": "aaahello", "c": "a"},
        expected="hello",
        msg="$ltrim should accept input and chars from document field paths",
    ),
    # Composite array: both from $arrayElemAt on a projected array-of-objects field.
    ExpressionTestCase(
        "field_composite_array",
        expression={
            "$ltrim": {
                "input": {"$arrayElemAt": ["$a.b", 0]},
                "chars": {"$arrayElemAt": ["$a.b", 1]},
            }
        },
        doc={"a": [{"b": "aaahello"}, {"b": "a"}]},
        expected="hello",
        msg="$ltrim should accept input and chars from composite array field paths",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LTRIM_FIELD_REF_TESTS))
def test_ltrim_field_refs(collection, test_case: ExpressionTestCase):
    """Test $ltrim with document field references."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
