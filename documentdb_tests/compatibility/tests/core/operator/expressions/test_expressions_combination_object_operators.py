"""
Nesting and interaction tests for $getField expression.

Representative samples of nested $getField, conditional field names,
sub-document access, and multiple $getField in one stage.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_chained",
        expression={
            "$getField": {
                "field": "b",
                "input": {"$getField": {"field": "a", "input": {"a": {"b": 42}}}},
            }
        },
        expected=42,
        msg="Should chain nested $getField through sub-documents",
    ),
    ExpressionTestCase(
        "nested_dotted_key",
        expression={
            "$getField": {
                "field": "x.y",
                "input": {
                    "$getField": {
                        "field": "a",
                        "input": {
                            "a": {"$setField": {"field": "x.y", "input": {}, "value": "found"}}
                        },
                    }
                },
            }
        },
        expected="found",
        msg="Should access dotted key from nested $getField result",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_getField_nesting_literal(collection, test):
    """Test nested $getField with literal inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dynamic_from_cond",
        expression={
            "$getField": {
                "field": {
                    "$cond": {"if": {"$eq": ["$type", "A"]}, "then": "fieldA", "else": "fieldB"}
                },
                "input": "$$CURRENT",
            }
        },
        doc={"type": "A", "fieldA": 1, "fieldB": 2},
        expected=1,
        msg="Should resolve $cond to field name",
    ),
    ExpressionTestCase(
        "subdocument_dollar_field",
        expression={"$getField": {"field": {"$literal": "$small"}, "input": "$quantity"}},
        doc={"quantity": {"$large": 50, "$medium": 30, "$small": 25}},
        expected=25,
        msg="Should access $-prefixed field from sub-document",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INSERT_TESTS))
def test_getField_nesting_insert(collection, test):
    """Test nested $getField with inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
