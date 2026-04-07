"""Tests for $divide operator — argument handling.

Covers argument count validation, per-input-position invalid types,
and per-input-position expression type tests.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assertExprResult,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params, with_expected
from documentdb_tests.framework.test_constants import (
    ARRAY_INPUT_ARGS,
    BSON_TYPE_SAMPLES,
    field_expression_cases,
)

# --- Argument count ---
ARG_COUNT_CASES = with_expected(
    ARRAY_INPUT_ARGS,
    default=EXPRESSION_TYPE_MISMATCH_ERROR,
    overrides={
        "2_args": None,
    },
)


@pytest.mark.parametrize("args, expected", ARG_COUNT_CASES)
def test_divide_argument_count(collection, args, expected):
    """Test $divide argument count validation."""
    collection.insert_one({"_placeholder": 1})
    result = execute_expression(collection, {"$divide": args})
    assertExprResult(result, expected)


# --- Non-numeric types: dividend (position 1) ---
DIVIDEND_TYPE_CASES = with_expected(
    BSON_TYPE_SAMPLES,
    default=TYPE_MISMATCH_ERROR,
    overrides={
        "null": None,
    },
)


@pytest.mark.parametrize("val, expected", DIVIDEND_TYPE_CASES)
def test_divide_dividend_type(collection, val, expected):
    """Test $divide behavior with non-numeric dividend types."""
    collection.insert_one({"a": val, "b": 2})
    result = execute_expression(collection, {"$divide": ["$a", "$b"]})
    assertExprResult(result, expected)


# --- Non-numeric types: divisor (position 2) ---
DIVISOR_TYPE_CASES = with_expected(
    BSON_TYPE_SAMPLES,
    default=TYPE_MISMATCH_ERROR,
    overrides={
        "null": None,
    },
)


@pytest.mark.parametrize("val, expected", DIVISOR_TYPE_CASES)
def test_divide_divisor_type(collection, val, expected):
    """Test $divide behavior with non-numeric divisor types."""
    collection.insert_one({"a": 10, "b": val})
    result = execute_expression(collection, {"$divide": ["$a", "$b"]})
    assertExprResult(result, expected)


# --- Expression types: dividend (position 1) ---
DIVIDEND_EXPR_CASES = field_expression_cases(
    value=10,
    expected={
        "missing_field": None,
        "nested_field": 5.0,
        "composite_array": TYPE_MISMATCH_ERROR,
        "index_object_key": 5.0,
        "index_array": TYPE_MISMATCH_ERROR,
        "array_expr": TYPE_MISMATCH_ERROR,
        "object_expr": TYPE_MISMATCH_ERROR,
    },
)


@pytest.mark.parametrize("expr, doc, expected", DIVIDEND_EXPR_CASES)
def test_divide_dividend_expr_type(collection, expr, doc, expected):
    """Test $divide dividend with different expression types."""
    collection.insert_one(doc)
    result = execute_expression(collection, {"$divide": [expr, 2]})
    assertExprResult(result, expected)


# --- Expression types: divisor (position 2) ---
DIVISOR_EXPR_CASES = field_expression_cases(
    value=2,
    expected={
        "missing_field": None,
        "nested_field": 5.0,
        "composite_array": TYPE_MISMATCH_ERROR,
        "index_object_key": 5.0,
        "index_array": TYPE_MISMATCH_ERROR,
        "array_expr": TYPE_MISMATCH_ERROR,
        "object_expr": TYPE_MISMATCH_ERROR,
    },
)


@pytest.mark.parametrize("expr, doc, expected", DIVISOR_EXPR_CASES)
def test_divide_divisor_expr_type(collection, expr, doc, expected):
    """Test $divide divisor with different expression types."""
    collection.insert_one(doc)
    result = execute_expression(collection, {"$divide": [10, expr]})
    assertExprResult(result, expected)


# --- Nested operator (self-nesting) ---
NESTED_OPERATOR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_dividend",
        expression={"$divide": [{"$divide": ["$val", 1]}, "$d"]},
        doc={"val": 10, "d": 2},
        expected=5.0,
        msg="Nested $divide in dividend resolves to numeric",
    ),
    ExpressionTestCase(
        "nested_divisor",
        expression={"$divide": ["$d", {"$divide": ["$val", 1]}]},
        doc={"val": 2, "d": 10},
        expected=5.0,
        msg="Nested $divide in divisor resolves to numeric",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NESTED_OPERATOR_TESTS))
def test_divide_nested_operator(collection, test):
    """Test $divide with self-nested operator expressions."""
    collection.insert_one(test.doc)
    result = execute_expression(collection, test.expression)
    assertExprResult(result, test.expected, msg=test.msg)
