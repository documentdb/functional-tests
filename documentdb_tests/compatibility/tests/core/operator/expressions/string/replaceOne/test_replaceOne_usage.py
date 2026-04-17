from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

from ...utils.expression_test_case import (
    ExpressionTestCase,
)
from .utils.replaceOne_common import (
    ReplaceOneTest,
    _expr,
)

# Property [Expression Arguments]: all three parameters accept arbitrary
# expressions that resolve to string or null.
REPLACEONE_EXPR_TESTS: list[ReplaceOneTest] = [
    ReplaceOneTest(
        "expr_input_expression",
        input={"$toUpper": "hello world"},
        find="WORLD",
        replacement="X",
        expected="HELLO X",
        msg="$replaceOne should accept input expression",
    ),
    ReplaceOneTest(
        "expr_find_expression",
        input="HELLO WORLD",
        find={"$toUpper": "world"},
        replacement="X",
        expected="HELLO X",
        msg="$replaceOne should accept find expression",
    ),
    ReplaceOneTest(
        "expr_replacement_expression",
        input="hello world",
        find="world",
        replacement={"$toUpper": "earth"},
        expected="hello EARTH",
        msg="$replaceOne should accept replacement expression",
    ),
    ReplaceOneTest(
        "expr_all_expressions",
        input={"$concat": ["hel", "lo"]},
        find={"$toLower": "LO"},
        replacement={"$toUpper": "p"},
        expected="helP",
        msg="$replaceOne should accept all expressions",
    ),
    # Expression resolving to null follows null propagation.
    ReplaceOneTest(
        "expr_null_input",
        input={"$literal": None},
        find="a",
        replacement="b",
        expected=None,
        msg="$replaceOne should accept null input",
    ),
    ReplaceOneTest(
        "expr_null_find",
        input="hello",
        find={"$literal": None},
        replacement="b",
        expected=None,
        msg="$replaceOne should accept null find",
    ),
    ReplaceOneTest(
        "expr_null_replacement",
        input="hello",
        find="h",
        replacement={"$literal": None},
        expected=None,
        msg="$replaceOne should accept null replacement",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REPLACEONE_EXPR_TESTS))
def test_replaceone_usage_cases(collection, test_case: ReplaceOneTest):
    """Test $replaceOne expression argument cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


# Property [Document Field References]: $replaceOne works with field references
# from inserted documents, not just inline literals.
REPLACEONE_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    # Object expression: all args from simple field paths.
    ExpressionTestCase(
        "field_object",
        expression={"$replaceOne": {"input": "$i", "find": "$f", "replacement": "$r"}},
        doc={"i": "cat bat cat", "f": "cat", "r": "dog"},
        expected="dog bat cat",
        msg="$replaceOne should accept args from document field paths",
    ),
    # Composite array: all args from $arrayElemAt on a projected array-of-objects field.
    ExpressionTestCase(
        "field_composite_array",
        expression={
            "$replaceOne": {
                "input": {"$arrayElemAt": ["$a.b", 0]},
                "find": {"$arrayElemAt": ["$a.b", 1]},
                "replacement": {"$arrayElemAt": ["$a.b", 2]},
            }
        },
        doc={"a": [{"b": "cat bat cat"}, {"b": "cat"}, {"b": "dog"}]},
        expected="dog bat cat",
        msg="$replaceOne should accept args from composite array field paths",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REPLACEONE_FIELD_REF_TESTS))
def test_replaceone_field_refs(collection, test_case: ExpressionTestCase):
    """Test $replaceOne with document field references."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
