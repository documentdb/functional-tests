from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.rtrim.utils.rtrim_common import (
    RtrimTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import ExpressionTestCase
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_expression_with_insert,
)

# Property [Expression Arguments]: input and chars accept any expression that resolves to a
# string. Nested $rtrim expressions are also accepted.
RTRIM_EXPR_TESTS: list[RtrimTest] = [
    # input is an expression.
    RtrimTest(
        "expr_input_concat",
        input={"$concat": ["hello", "  "]},
        expected="hello",
        msg="$rtrim should accept $concat expression as input",
    ),
    # chars is an expression.
    RtrimTest(
        "expr_chars_concat",
        input="helloaaa",
        chars={"$concat": ["a"]},
        expected="hello",
        msg="$rtrim should accept $concat expression as chars",
    ),
    # Both input and chars are expressions.
    RtrimTest(
        "expr_both",
        input={"$concat": ["hello", "xx"]},
        chars={"$concat": ["x"]},
        expected="hello",
        msg="$rtrim should accept expressions for both input and chars",
    ),
    # Nested $rtrim as input to another $rtrim.
    RtrimTest(
        "expr_nested_rtrim",
        input={"$rtrim": {"input": "helloaa  "}},
        chars="a",
        expected="hello",
        msg="$rtrim should accept nested $rtrim as input expression",
    ),
    # $literal for dollar-prefixed strings.
    RtrimTest(
        "expr_literal_dollar",
        input={"$literal": "hello$$$"},
        chars={"$literal": "$"},
        expected="hello",
        msg="$rtrim should accept $literal for dollar-prefixed strings",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(RTRIM_EXPR_TESTS))
def test_rtrim_input_forms(collection, test_case: RtrimTest):
    """Test $rtrim expression arguments."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


# Property [Document Field References]: $rtrim works with field references
# from inserted documents, not just inline literals.
RTRIM_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    # Object expression: both input and chars from simple field paths.
    ExpressionTestCase(
        "field_object",
        expression={"$rtrim": {"input": "$s", "chars": "$c"}},
        doc={"s": "helloaaa", "c": "a"},
        expected="hello",
        msg="$rtrim should accept input and chars from document field paths",
    ),
    # Composite array: both from $arrayElemAt on a projected array-of-objects field.
    ExpressionTestCase(
        "field_composite_array",
        expression={
            "$rtrim": {
                "input": {"$arrayElemAt": ["$a.b", 0]},
                "chars": {"$arrayElemAt": ["$a.b", 1]},
            }
        },
        doc={"a": [{"b": "helloaaa"}, {"b": "a"}]},
        expected="hello",
        msg="$rtrim should accept input and chars from composite array field paths",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(RTRIM_FIELD_REF_TESTS))
def test_rtrim_field_refs(collection, test_case: ExpressionTestCase):
    """Test $rtrim with document field references."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
