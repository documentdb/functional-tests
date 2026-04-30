"""Tests for $divide operator — argument handling.

Covers argument count validation and per-input-position invalid type tests
using shared BSON_TYPE_SAMPLES and ARRAY_INPUT_ARGS constants.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result_v2,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import with_expected
from documentdb_tests.framework.test_constants import ARRAY_INPUT_ARGS, BSON_TYPE_SAMPLES

ERR = TYPE_MISMATCH_ERROR

# --- Argument count ---


@pytest.mark.parametrize("args", [a for a in ARRAY_INPUT_ARGS if a.id != "2_args"])
def test_divide_argument_count(collection, args):
    """Test $divide rejects wrong argument counts."""
    result = execute_expression(collection, {"$divide": args})
    assert_expression_result_v2(result, EXPRESSION_TYPE_MISMATCH_ERROR)


# --- Non-numeric types: dividend (position 1) ---
DIVIDEND_TYPE_CASES = with_expected(
    BSON_TYPE_SAMPLES,
    expected_list={
        "string": ERR,
        "bool": ERR,
        "int32": 0.5,
        "int64": 0.5,
        "double": 0.5,
        "decimal128": Decimal128("0.5"),
        "array": ERR,
        "object": ERR,
        "empty_array": ERR,
        "empty_object": ERR,
        "date": ERR,
        "objectid": ERR,
        "regex": ERR,
        "code": ERR,
        "timestamp": ERR,
        "minkey": ERR,
        "maxkey": ERR,
        "bindata": ERR,
        "null": None,
    },
)


@pytest.mark.parametrize("val, expected", DIVIDEND_TYPE_CASES)
def test_divide_dividend_type(collection, val, expected):
    """Test $divide behavior with each BSON type as dividend."""
    result = execute_expression_with_insert(
        collection,
        {"$divide": ["$a", "$b"]},
        {"a": val, "b": 2},
    )
    assert_expression_result_v2(result, expected)


# --- Non-numeric types: divisor (position 2) ---
DIVISOR_TYPE_CASES = with_expected(
    BSON_TYPE_SAMPLES,
    expected_list={
        "string": ERR,
        "bool": ERR,
        "int32": 10.0,
        "int64": 10.0,
        "double": 10.0,
        "decimal128": Decimal128("10"),
        "array": ERR,
        "object": ERR,
        "empty_array": ERR,
        "empty_object": ERR,
        "date": ERR,
        "objectid": ERR,
        "regex": ERR,
        "code": ERR,
        "timestamp": ERR,
        "minkey": ERR,
        "maxkey": ERR,
        "bindata": ERR,
        "null": None,
    },
)


@pytest.mark.parametrize("val, expected", DIVISOR_TYPE_CASES)
def test_divide_divisor_type(collection, val, expected):
    """Test $divide behavior with each BSON type as divisor."""
    result = execute_expression_with_insert(
        collection,
        {"$divide": ["$a", "$b"]},
        {"a": 10, "b": val},
    )
    assert_expression_result_v2(result, expected)
