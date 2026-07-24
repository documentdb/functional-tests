"""
Error tests for $arrayElemAt expression.

Tests non-array first argument, non-numeric index, non-integral numeric index,
and wrong arity errors.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
    ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
    ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_OVERFLOW,
    INT64_MAX,
    INT64_MIN,
)

# Property [Array Type Strictness]: $arrayElemAt rejects a non-array first argument.
ARRAY_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_as_array",
        doc={"arr": "hello", "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject string as array",
    ),
    ExpressionTestCase(
        id="int_as_array",
        doc={"arr": 42, "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject int as array",
    ),
    ExpressionTestCase(
        id="bool_true_as_array",
        doc={"arr": True, "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject bool true as array",
    ),
    ExpressionTestCase(
        id="bool_false_as_array",
        doc={"arr": False, "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject bool false as array",
    ),
    ExpressionTestCase(
        id="object_as_array",
        doc={"arr": {"a": 1}, "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject object as array",
    ),
    ExpressionTestCase(
        id="double_as_array",
        doc={"arr": 3.14, "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject double as array",
    ),
    ExpressionTestCase(
        id="decimal128_as_array",
        doc={"arr": Decimal128("1"), "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject decimal128 as array",
    ),
    ExpressionTestCase(
        id="int64_as_array",
        doc={"arr": Int64(1), "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject int64 as array",
    ),
    ExpressionTestCase(
        id="binary_as_array",
        doc={"arr": Binary(b"x", 0), "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject binary as array",
    ),
    ExpressionTestCase(
        id="datetime_as_array",
        doc={"arr": datetime(2024, 1, 1, tzinfo=timezone.utc), "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject datetime as array",
    ),
    ExpressionTestCase(
        id="objectid_as_array",
        doc={"arr": ObjectId(), "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject objectid as array",
    ),
    ExpressionTestCase(
        id="regex_as_array",
        doc={"arr": Regex("x"), "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject regex as array",
    ),
    ExpressionTestCase(
        id="maxkey_as_array",
        doc={"arr": MaxKey(), "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject maxkey as array",
    ),
    ExpressionTestCase(
        id="minkey_as_array",
        doc={"arr": MinKey(), "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject minkey as array",
    ),
    ExpressionTestCase(
        id="timestamp_as_array",
        doc={"arr": Timestamp(0, 0), "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject timestamp as array",
    ),
    ExpressionTestCase(
        id="nan_as_array",
        doc={"arr": FLOAT_NAN, "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject NaN as array",
    ),
    ExpressionTestCase(
        id="inf_as_array",
        doc={"arr": FLOAT_INFINITY, "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject Infinity as array",
    ),
    ExpressionTestCase(
        id="decimal128_nan_as_array",
        doc={"arr": DECIMAL128_NAN, "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject Decimal128 NaN as array",
    ),
    ExpressionTestCase(
        id="decimal128_inf_as_array",
        doc={"arr": DECIMAL128_INFINITY, "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$arrayElemAt should reject Decimal128 Infinity as array",
    ),
]

# Property [Index Type Strictness]: $arrayElemAt rejects a non-numeric index.
INDEX_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_index",
        doc={"arr": [1, 2], "idx": "0"},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject string index",
    ),
    ExpressionTestCase(
        id="bool_true_index",
        doc={"arr": [1, 2], "idx": True},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject bool true index",
    ),
    ExpressionTestCase(
        id="bool_false_index",
        doc={"arr": [1, 2], "idx": False},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject bool false index",
    ),
    ExpressionTestCase(
        id="array_index",
        doc={"arr": [1, 2], "idx": [0]},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject array index",
    ),
    ExpressionTestCase(
        id="object_index",
        doc={"arr": [1, 2], "idx": {"a": 0}},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject object index",
    ),
    ExpressionTestCase(
        id="objectid_index",
        doc={"arr": [1, 2], "idx": ObjectId()},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject objectid index",
    ),
    ExpressionTestCase(
        id="binary_index",
        doc={"arr": [1, 2], "idx": Binary(b"\x01", 0)},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject binary index",
    ),
    ExpressionTestCase(
        id="timestamp_index",
        doc={"arr": [1, 2], "idx": Timestamp(0, 0)},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject timestamp index",
    ),
    ExpressionTestCase(
        id="datetime_index",
        doc={"arr": [1, 2], "idx": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject datetime index",
    ),
    ExpressionTestCase(
        id="maxkey_index",
        doc={"arr": [1, 2], "idx": MaxKey()},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject maxkey index",
    ),
    ExpressionTestCase(
        id="minkey_index",
        doc={"arr": [1, 2], "idx": MinKey()},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject minkey index",
    ),
    ExpressionTestCase(
        id="regex_index",
        doc={"arr": [1, 2], "idx": Regex("x")},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR,
        msg="$arrayElemAt should reject regex index",
    ),
]

# Property [Integral Index]: $arrayElemAt rejects a non-integral or out-of-range numeric index.
NON_INTEGRAL_INDEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="double_fractional_index",
        doc={"arr": [1, 2, 3], "idx": 1.5},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject fractional double index",
    ),
    ExpressionTestCase(
        id="decimal128_fractional_index",
        doc={"arr": [1, 2, 3], "idx": DECIMAL128_HALF},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject fractional decimal128 index",
    ),
    ExpressionTestCase(
        id="double_nan_index",
        doc={"arr": [1, 2, 3], "idx": FLOAT_NAN},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject NaN index",
    ),
    ExpressionTestCase(
        id="double_inf_index",
        doc={"arr": [1, 2, 3], "idx": FLOAT_INFINITY},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject infinity index",
    ),
    ExpressionTestCase(
        id="double_neg_inf_index",
        doc={"arr": [1, 2, 3], "idx": FLOAT_NEGATIVE_INFINITY},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject -infinity index",
    ),
    ExpressionTestCase(
        id="decimal128_nan_index",
        doc={"arr": [1, 2, 3], "idx": DECIMAL128_NAN},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject decimal128 NaN index",
    ),
    ExpressionTestCase(
        id="decimal128_inf_index",
        doc={"arr": [1, 2, 3], "idx": DECIMAL128_INFINITY},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject decimal128 infinity index",
    ),
    ExpressionTestCase(
        id="decimal128_neg_inf_index",
        doc={"arr": [1, 2, 3], "idx": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject decimal128 -infinity index",
    ),
    ExpressionTestCase(
        id="int64_max_index",
        doc={"arr": [1, 2, 3], "idx": INT64_MAX},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject INT64_MAX index",
    ),
    ExpressionTestCase(
        id="int64_min_index",
        doc={"arr": [1, 2, 3], "idx": INT64_MIN},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject INT64_MIN index",
    ),
    ExpressionTestCase(
        id="large_double_index",
        doc={"arr": [1, 2, 3], "idx": 1.0e18},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject large double index",
    ),
    ExpressionTestCase(
        id="large_neg_double_index",
        doc={"arr": [1, 2, 3], "idx": -1.0e18},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject large negative double index",
    ),
    ExpressionTestCase(
        id="decimal128_beyond_int32",
        doc={"arr": [1, 2, 3], "idx": Decimal128(str(INT32_OVERFLOW))},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject decimal128 beyond int32",
    ),
    ExpressionTestCase(
        id="decimal128_huge",
        doc={"arr": [1, 2, 3], "idx": DECIMAL128_INT64_OVERFLOW},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        error_code=ARRAY_ELEM_AT_INDEX_NOT_INTEGRAL_ERROR,
        msg="$arrayElemAt should reject huge decimal128 index",
    ),
]

ALL_TESTS = ARRAY_TYPE_ERROR_TESTS + INDEX_TYPE_ERROR_TESTS + NON_INTEGRAL_INDEX_TESTS

# Property [Arity]: $arrayElemAt requires exactly two arguments.
ARITY_ERROR_TESTS = [
    pytest.param({"$arrayElemAt": [[1, 2, 3]]}, id="one_arg"),
    pytest.param({"$arrayElemAt": [[1, 2, 3], 0, 1]}, id="three_args"),
    pytest.param({"$arrayElemAt": []}, id="zero_args"),
    pytest.param({"$arrayElemAt": [[[1, 2, 3], 0]]}, id="nested_pair_not_flattened_to_two_args"),
]


@pytest.mark.parametrize("expr", ARITY_ERROR_TESTS)
def test_arrayElemAt_syntax_error(collection, expr):
    """Test $arrayElemAt errors with wrong number of arguments."""
    result = execute_expression(collection, expr)
    assert_expression_result(result, error_code=EXPRESSION_TYPE_MISMATCH_ERROR)


# Property [Index Type Strictness]: $arrayElemAt rejects a field path that resolves to an
# array as the index argument.
def test_arrayElemAt_composite_array_as_index(collection):
    """Test $arrayElemAt rejects a composite array from $x.y as the index argument."""
    result = execute_expression_with_insert(
        collection, {"$arrayElemAt": [[10, 20, 30], "$x.y"]}, {"x": [{"y": 0}, {"y": 1}]}
    )
    assert_expression_result(result, error_code=ARRAY_ELEM_AT_INDEX_TYPE_ERROR)
