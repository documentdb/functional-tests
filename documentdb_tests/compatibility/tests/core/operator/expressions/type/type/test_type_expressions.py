"""$type expression argument and return type tests.

Tests that $type accepts any expression as its argument (returning the BSON
type of the resolved value) and always returns a value of BSON type 'string'.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Arguments]: $type accepts any expression that resolves
# to a value and returns the BSON type of the resolved result.
TYPE_EXPRESSION_ARGS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "expr_returns_int",
        expression={"$type": {"$add": [1, 2]}},
        expected="int",
        msg="$type should return 'int' for an expression resolving to int",
    ),
    ExpressionTestCase(
        "expr_returns_long",
        expression={"$type": {"$add": [Int64(1), Int64(2)]}},
        expected="long",
        msg="$type should return 'long' for an expression resolving to long",
    ),
    ExpressionTestCase(
        "expr_returns_double",
        expression={"$type": {"$divide": [1, 2]}},
        expected="double",
        msg="$type should return 'double' for an expression resolving to double",
    ),
    ExpressionTestCase(
        "expr_returns_decimal",
        expression={"$type": {"$add": [Decimal128("1"), Decimal128("2")]}},
        expected="decimal",
        msg="$type should return 'decimal' for an expression resolving to decimal",
    ),
    ExpressionTestCase(
        "expr_returns_string",
        expression={"$type": {"$concat": ["a", "b"]}},
        expected="string",
        msg="$type should return 'string' for an expression resolving to string",
    ),
    ExpressionTestCase(
        "expr_returns_bool",
        expression={"$type": {"$gt": [2, 1]}},
        expected="bool",
        msg="$type should return 'bool' for an expression resolving to bool",
    ),
    ExpressionTestCase(
        "expr_returns_date",
        expression={"$type": {"$dateFromString": {"dateString": "2024-01-01"}}},
        expected="date",
        msg="$type should return 'date' for an expression resolving to date",
    ),
    ExpressionTestCase(
        "expr_returns_null",
        expression={"$type": {"$ifNull": [None, None]}},
        expected="null",
        msg="$type should return 'null' for an expression resolving to null",
    ),
    ExpressionTestCase(
        "expr_returns_object",
        expression={"$type": {"$mergeObjects": [{"a": 1}, {"b": 2}]}},
        expected="object",
        msg="$type should return 'object' for an expression resolving to object",
    ),
    ExpressionTestCase(
        "expr_returns_array",
        expression={"$type": {"$concatArrays": [[1], [2]]}},
        expected="array",
        msg="$type should return 'array' for an expression resolving to array",
    ),
]

# Property [Return Type]: $type always returns a value of type "string",
# regardless of the input type.
TYPE_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_is_string",
        expression={"$type": {"$type": 42}},
        expected="string",
        msg="$type should itself return a string value",
    ),
]

TYPE_EXPRESSION_TESTS = TYPE_EXPRESSION_ARGS_TESTS + TYPE_RETURN_TYPE_TESTS


@pytest.mark.parametrize("test", pytest_params(TYPE_EXPRESSION_TESTS))
def test_type_expressions(collection, test: ExpressionTestCase):
    """$type returns the correct type name for values produced by expressions."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
