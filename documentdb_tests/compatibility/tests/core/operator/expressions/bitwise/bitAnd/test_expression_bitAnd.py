"""
Tests for $bitAnd expression type smoke tests.

Covers literal, field reference, and nested expression operator inputs.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (
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
        "literal_bit_and",
        expression={"$bitAnd": [5, 3]},
        expected=1,
        msg="$bitAnd of two literals should compute the bitwise AND result",
    ),
    ExpressionTestCase(
        "literal_bit_and_with_zero",
        expression={"$bitAnd": [0, 7]},
        expected=0,
        msg="$bitAnd with zero should produce zero",
    ),
]

FIELD_REFERENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_reference_bit_and",
        expression={"$bitAnd": ["$a", "$b"]},
        doc={"a": 5, "b": 3},
        expected=1,
        msg="$bitAnd should compute the bitwise AND of two field values",
    ),
    ExpressionTestCase(
        "field_reference_bit_and_secondary",
        expression={"$bitAnd": ["$a", "$b"]},
        doc={"a": 12, "b": 10},
        expected=8,
        msg="$bitAnd should compute the bitwise AND for other field values",
    ),
]

EXPRESSION_OPERATOR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_expression_bit_and",
        expression={
            "$bitAnd": [
                {"$add": ["$a", 1]},
                {"$subtract": ["$b", 1]},
            ]
        },
        doc={"a": 4, "b": 6},
        expected=5,
        msg="$bitAnd should accept nested expression operator inputs",
    ),
]

ALL_INSERT_TESTS = FIELD_REFERENCE_TESTS + EXPRESSION_OPERATOR_TESTS


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_bitAnd_expression_types_literal(collection, test):
    """Test $bitAnd with literal expression inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(ALL_INSERT_TESTS))
def test_bitAnd_expression_types_insert(collection, test):
    """Test $bitAnd with field reference and nested expression inputs."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
