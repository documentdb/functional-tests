"""Tests for $divide operator — argument handling.

Covers argument count validation, per-input-position invalid types,
and expression type smoke tests.
"""

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Code, MaxKey, MinKey, ObjectId, Regex, Timestamp
from datetime import datetime

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.test_case import BaseTestCase, pytest_params


@dataclass(frozen=True)
class DivideTest(BaseTestCase):
    """Test case for $divide with dividend/divisor fields."""

    dividend: Any = None
    divisor: Any = None


# --- Argument count ---
ARG_COUNT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "no_args",
        expression={"$divide": []},
        doc={},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$divide with 0 args → error",
    ),
    ExpressionTestCase(
        "one_arg",
        expression={"$divide": ["$a"]},
        doc={"a": 10},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$divide with 1 arg → error",
    ),
    ExpressionTestCase(
        "three_args",
        expression={"$divide": ["$a", "$b", "$c"]},
        doc={"a": 10, "b": 2, "c": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$divide with 3 args → error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARG_COUNT_TESTS))
def test_divide_argument_count(collection, test):
    """Test $divide rejects wrong argument counts."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assertResult(result, error_code=test.error_code, msg=test.msg)


# --- Invalid types: dividend (position 1) ---
INVALID_DIVIDEND_TESTS: list[DivideTest] = [
    DivideTest(
        "string_dividend",
        dividend="str",
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="string dividend → error",
    ),
    DivideTest(
        "bool_dividend",
        dividend=True,
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="bool dividend → error",
    ),
    DivideTest(
        "array_dividend",
        dividend=[1, 2],
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="array dividend → error",
    ),
    DivideTest(
        "object_dividend",
        dividend={"x": 1},
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="object dividend → error",
    ),
    DivideTest(
        "empty_array_dividend",
        dividend=[],
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="empty array dividend → error",
    ),
    DivideTest(
        "empty_object_dividend",
        dividend={},
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="empty object dividend → error",
    ),
    DivideTest(
        "date_dividend",
        dividend=datetime(2024, 1, 1),
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="date dividend → error",
    ),
    DivideTest(
        "objectid_dividend",
        dividend=ObjectId(),
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="objectId dividend → error",
    ),
    DivideTest(
        "regex_dividend",
        dividend=Regex(".*"),
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="regex dividend → error",
    ),
    DivideTest(
        "code_dividend",
        dividend=Code("function(){}"),
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="javascript dividend → error",
    ),
    DivideTest(
        "timestamp_dividend",
        dividend=Timestamp(0, 0),
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="timestamp dividend → error",
    ),
    DivideTest(
        "minkey_dividend",
        dividend=MinKey(),
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="minKey dividend → error",
    ),
    DivideTest(
        "maxkey_dividend",
        dividend=MaxKey(),
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxKey dividend → error",
    ),
    DivideTest(
        "bindata_dividend",
        dividend=b"\x00",
        divisor=2,
        error_code=TYPE_MISMATCH_ERROR,
        msg="binData dividend → error",
    ),
]

# --- Invalid types: divisor (position 2) ---
INVALID_DIVISOR_TESTS: list[DivideTest] = [
    DivideTest(
        "string_divisor",
        dividend=10,
        divisor="str",
        error_code=TYPE_MISMATCH_ERROR,
        msg="string divisor → error",
    ),
    DivideTest(
        "bool_divisor",
        dividend=10,
        divisor=True,
        error_code=TYPE_MISMATCH_ERROR,
        msg="bool divisor → error",
    ),
    DivideTest(
        "array_divisor",
        dividend=10,
        divisor=[1, 2],
        error_code=TYPE_MISMATCH_ERROR,
        msg="array divisor → error",
    ),
    DivideTest(
        "object_divisor",
        dividend=10,
        divisor={"x": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="object divisor → error",
    ),
    DivideTest(
        "empty_array_divisor",
        dividend=10,
        divisor=[],
        error_code=TYPE_MISMATCH_ERROR,
        msg="empty array divisor → error",
    ),
    DivideTest(
        "empty_object_divisor",
        dividend=10,
        divisor={},
        error_code=TYPE_MISMATCH_ERROR,
        msg="empty object divisor → error",
    ),
    DivideTest(
        "date_divisor",
        dividend=10,
        divisor=datetime(2024, 1, 1),
        error_code=TYPE_MISMATCH_ERROR,
        msg="date divisor → error",
    ),
    DivideTest(
        "objectid_divisor",
        dividend=10,
        divisor=ObjectId(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="objectId divisor → error",
    ),
    DivideTest(
        "regex_divisor",
        dividend=10,
        divisor=Regex(".*"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="regex divisor → error",
    ),
    DivideTest(
        "code_divisor",
        dividend=10,
        divisor=Code("function(){}"),
        error_code=TYPE_MISMATCH_ERROR,
        msg="javascript divisor → error",
    ),
    DivideTest(
        "timestamp_divisor",
        dividend=10,
        divisor=Timestamp(0, 0),
        error_code=TYPE_MISMATCH_ERROR,
        msg="timestamp divisor → error",
    ),
    DivideTest(
        "minkey_divisor",
        dividend=10,
        divisor=MinKey(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="minKey divisor → error",
    ),
    DivideTest(
        "maxkey_divisor",
        dividend=10,
        divisor=MaxKey(),
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxKey divisor → error",
    ),
    DivideTest(
        "bindata_divisor",
        dividend=10,
        divisor=b"\x00",
        error_code=TYPE_MISMATCH_ERROR,
        msg="binData divisor → error",
    ),
]

# --- Expression type smoke tests ---
EXPRESSION_SMOKE_TESTS: list[DivideTest] = [
    DivideTest("field_ref", dividend=10, divisor=2, expected=5.0, msg="Field reference inputs"),
    DivideTest(
        "frac_result", dividend=5, divisor=10, expected=0.5, msg="Fractional result from fields"
    ),
]

TYPE_TESTS = INVALID_DIVIDEND_TESTS + INVALID_DIVISOR_TESTS + EXPRESSION_SMOKE_TESTS


@pytest.mark.parametrize("test", pytest_params(TYPE_TESTS))
def test_divide_type_validation(collection, test):
    """Test $divide type validation per input position."""
    result = execute_expression_with_insert(
        collection,
        {"$divide": ["$dividend", "$divisor"]},
        {"dividend": test.dividend, "divisor": test.divisor},
    )
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)


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
        "nested_expr",
        expression={"$divide": [{"$abs": "$a"}, {"$abs": "$b"}]},
        doc={"a": -10, "b": -2},
        expected=5.0,
        msg="Expression operator inputs",
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
    assertResult(result, expected=test.expected, msg=test.msg)
