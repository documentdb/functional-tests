"""Tests for $divide operator — argument handling.

Covers argument count validation, per-input-position invalid types,
and expression type smoke tests.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assertExprResult,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params, with_expected
from documentdb_tests.framework.test_constants import ARRAY_INPUT_ARGS, BSON_TYPE_SAMPLES

ERR = TYPE_MISMATCH_ERROR

# --- Argument count ---


@pytest.mark.parametrize("args", [a for a in ARRAY_INPUT_ARGS if a.id != "2_args"])
def test_divide_argument_count(collection, args):
    """Test $divide rejects wrong argument counts."""
    result = execute_expression(collection, {"$divide": args})
    assertExprResult(result, EXPRESSION_TYPE_MISMATCH_ERROR)


# --- Non-numeric types: dividend (position 1) ---
DIVIDEND_TYPE_CASES = with_expected(BSON_TYPE_SAMPLES, expected_list={
    "string": ERR, "bool": ERR, "array": ERR, "object": ERR,
    "empty_array": ERR, "empty_object": ERR, "date": ERR, "objectid": ERR,
    "regex": ERR, "code": ERR, "timestamp": ERR, "minkey": ERR,
    "maxkey": ERR, "bindata": ERR, "null": None,
})


@pytest.mark.parametrize("val, expected", DIVIDEND_TYPE_CASES)
def test_divide_dividend_type(collection, val, expected):
    """Test $divide behavior with non-numeric dividend types."""
    result = execute_expression_with_insert(
        collection, {"$divide": ["$a", "$b"]}, {"a": val, "b": 2},
    )
    assertExprResult(result, expected)


# --- Non-numeric types: divisor (position 2) ---
DIVISOR_TYPE_CASES = with_expected(BSON_TYPE_SAMPLES, expected_list={
    "string": ERR, "bool": ERR, "array": ERR, "object": ERR,
    "empty_array": ERR, "empty_object": ERR, "date": ERR, "objectid": ERR,
    "regex": ERR, "code": ERR, "timestamp": ERR, "minkey": ERR,
    "maxkey": ERR, "bindata": ERR, "null": None,
})


@pytest.mark.parametrize("val, expected", DIVISOR_TYPE_CASES)
def test_divide_divisor_type(collection, val, expected):
    """Test $divide behavior with non-numeric divisor types."""
    result = execute_expression_with_insert(
        collection, {"$divide": ["$a", "$b"]}, {"a": 10, "b": val},
    )
    assertExprResult(result, expected)


# --- Expression nesting smoke ---
NESTING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_input",
        expression={"$divide": [10, 2]},
        doc={},
        expected=5.0,
        msg="Literal inputs",
    ),
    ExpressionTestCase(
        "nested_divide",
        expression={"$divide": [{"$divide": ["$a", "$b"]}, "$c"]},
        doc={"a": 100, "b": 2, "c": 5},
        expected=10.0,
        msg="Nested $divide",
    ),
    ExpressionTestCase(
        "nested_field",
        expression={"$divide": ["$x.y", "$z.w"]},
        doc={"x": {"y": 10}, "z": {"w": 2}},
        expected=5.0,
        msg="Nested field paths",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NESTING_TESTS))
def test_divide_expression_nesting(collection, test):
    """Test $divide with nested expressions and field paths."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assertExprResult(result, test.expected, msg=test.msg)
