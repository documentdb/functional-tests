"""
Error tests for $slice expression.

Tests non-array first argument, non-numeric/non-integral n, non-positive n
in 3-arg form, wrong arity errors, and a field path resolving to an
invalid-type n. Position-argument errors are in test_expression_slice_position_errors.py.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_ARITY_ERROR,
    EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
    EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
    EXPRESSION_SLICE_N_NOT_POSITIVE_ERROR,
    SLICE_INVALID_ARGUMENT_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_MAX,
)

# Property [Positive n Required]: in the 3-arg form, a non-positive n is rejected.
N_NOT_POSITIVE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pos_0_n_0",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": 0, "n": 0},
        error_code=EXPRESSION_SLICE_N_NOT_POSITIVE_ERROR,
        msg="$slice should reject n=0 in the 3-arg form",
    ),
    ExpressionTestCase(
        "pos_1_n_0",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": 1, "n": 0},
        error_code=EXPRESSION_SLICE_N_NOT_POSITIVE_ERROR,
        msg="$slice should reject n=0 with position 1",
    ),
    ExpressionTestCase(
        "pos_0_n_neg",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": 0, "n": -1},
        error_code=EXPRESSION_SLICE_N_NOT_POSITIVE_ERROR,
        msg="$slice should reject negative n in the 3-arg form",
    ),
    ExpressionTestCase(
        "pos_1_n_neg",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": 1, "n": -2},
        error_code=EXPRESSION_SLICE_N_NOT_POSITIVE_ERROR,
        msg="$slice should reject n=-2 in the 3-arg form",
    ),
    ExpressionTestCase(
        "neg_pos_n_neg",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": -1, "n": -1},
        error_code=EXPRESSION_SLICE_N_NOT_POSITIVE_ERROR,
        msg="$slice should reject negative n with a negative position",
    ),
    ExpressionTestCase(
        "n_neg_zero_double_3arg",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": 0, "n": DOUBLE_NEGATIVE_ZERO},
        error_code=EXPRESSION_SLICE_N_NOT_POSITIVE_ERROR,
        msg="$slice should reject -0.0 n in the 3-arg form",
    ),
    ExpressionTestCase(
        "n_neg_zero_decimal128_3arg",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": 0, "n": DECIMAL128_NEGATIVE_ZERO},
        error_code=EXPRESSION_SLICE_N_NOT_POSITIVE_ERROR,
        msg="$slice should reject Decimal128 -0 n in the 3-arg form",
    ),
]

# Property [Array Required]: a non-array, non-null first argument is rejected for every BSON type.
NOT_ARRAY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": "hello", "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject a string as the array argument",
    ),
    ExpressionTestCase(
        "int_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": 42, "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject an int as the array argument",
    ),
    ExpressionTestCase(
        "double_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": 3.14, "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject a double as the array argument",
    ),
    ExpressionTestCase(
        "bool_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": True, "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject a bool as the array argument",
    ),
    ExpressionTestCase(
        "object_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": {"a": 1}, "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject an object as the array argument",
    ),
    ExpressionTestCase(
        "decimal128_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": Decimal128("1"), "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject a decimal128 as the array argument",
    ),
    ExpressionTestCase(
        "int64_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": Int64(1), "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject an int64 as the array argument",
    ),
    ExpressionTestCase(
        "binary_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": Binary(b"x", 0), "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject a binary as the array argument",
    ),
    ExpressionTestCase(
        "datetime_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": datetime(2024, 1, 1, tzinfo=timezone.utc), "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject a datetime as the array argument",
    ),
    ExpressionTestCase(
        "objectid_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": ObjectId(), "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject an objectid as the array argument",
    ),
    ExpressionTestCase(
        "regex_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": Regex("x"), "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject a regex as the array argument",
    ),
    ExpressionTestCase(
        "javascript_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": Code("x"), "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject JavaScript code as the array argument",
    ),
    ExpressionTestCase(
        "timestamp_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": Timestamp(0, 0), "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject a timestamp as the array argument",
    ),
    ExpressionTestCase(
        "minkey_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": MinKey(), "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject minkey as the array argument",
    ),
    ExpressionTestCase(
        "maxkey_as_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": MaxKey(), "n": 1},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject maxkey as the array argument",
    ),
]

# Property [Numeric n]: a non-numeric n is rejected for every non-deprecated BSON type.
N_NOT_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "n_string",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": "2"},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject string n",
    ),
    ExpressionTestCase(
        "n_bool",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": True},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject bool n",
    ),
    ExpressionTestCase(
        "n_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": [2]},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject array n",
    ),
    ExpressionTestCase(
        "n_object",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": {"a": 2}},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject object n",
    ),
    ExpressionTestCase(
        "n_datetime",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject datetime n",
    ),
    ExpressionTestCase(
        "n_objectid",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": ObjectId()},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject objectid n",
    ),
    ExpressionTestCase(
        "n_binary",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": Binary(b"x", 0)},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject binary n",
    ),
    ExpressionTestCase(
        "n_regex",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": Regex("x")},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject regex n",
    ),
    ExpressionTestCase(
        "n_javascript",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": Code("x")},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject JavaScript code n",
    ),
    ExpressionTestCase(
        "n_timestamp",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": Timestamp(0, 0)},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject timestamp n",
    ),
    ExpressionTestCase(
        "n_minkey",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": MinKey()},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject minkey n",
    ),
    ExpressionTestCase(
        "n_maxkey",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": MaxKey()},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject maxkey n",
    ),
]

# Property [32-bit Representability]: n must be a whole number representable as a
# signed 32-bit integer; fractional values, NaN/Infinity, and integral values outside
# the int32 range are all rejected with the same error.
N_NOT_INTEGRAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "n_fractional_double",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": 1.5},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject a fractional double n",
    ),
    ExpressionTestCase(
        "n_fractional_decimal128",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": DECIMAL128_HALF},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject a fractional decimal128 n",
    ),
    ExpressionTestCase(
        "n_nan",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": FLOAT_NAN},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject NaN n",
    ),
    ExpressionTestCase(
        "n_inf",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": FLOAT_INFINITY},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject infinity n",
    ),
    ExpressionTestCase(
        "n_neg_inf",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": FLOAT_NEGATIVE_INFINITY},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject -infinity n",
    ),
    ExpressionTestCase(
        "n_decimal128_nan",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": DECIMAL128_NAN},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject decimal128 NaN n",
    ),
    ExpressionTestCase(
        "n_decimal128_inf",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": DECIMAL128_INFINITY},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject decimal128 infinity n",
    ),
    ExpressionTestCase(
        "n_int64_max",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": INT64_MAX},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject n that is a whole number outside the 32-bit integer range",
    ),
]

# Property [Field Expression n]: a field path that resolves to a non-numeric n is rejected.
FIELD_EXPR_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array_as_n",
        expression={"$slice": [[1, 2, 3], "$x.y"]},
        doc={"x": [{"y": 1}, {"y": 2}]},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject a composite array resolved as the n argument",
    ),
]

ALL_TESTS = (
    N_NOT_POSITIVE_ERROR_TESTS
    + NOT_ARRAY_ERROR_TESTS
    + N_NOT_NUMERIC_TESTS
    + N_NOT_INTEGRAL_TESTS
    + FIELD_EXPR_ERROR_TESTS
)

# Property [Literal Arguments]: errors are raised the same way with literal arguments.
LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_string_as_array",
        expression={"$slice": ["hello", 1]},
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice should reject a literal string as the array argument",
    ),
    ExpressionTestCase(
        "literal_pos_0_n_0",
        expression={"$slice": [[1, 2, 3], 0, 0]},
        error_code=EXPRESSION_SLICE_N_NOT_POSITIVE_ERROR,
        msg="$slice should reject literal n=0 in the 3-arg form",
    ),
    ExpressionTestCase(
        "literal_n_fractional_double",
        expression={"$slice": [[1, 2, 3], 1.5]},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject a literal fractional double n",
    ),
]

# Property [Arity]: $slice requires exactly two or three arguments.
ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_args",
        expression={"$slice": []},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$slice should reject zero arguments",
    ),
    ExpressionTestCase(
        "one_arg",
        expression={"$slice": [[1, 2, 3]]},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$slice should reject a single argument",
    ),
    ExpressionTestCase(
        "four_args",
        expression={"$slice": [[1, 2, 3], 0, 2, 1]},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$slice should reject four arguments",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS + ARITY_ERROR_TESTS))
def test_slice_literal(collection, test):
    """Test $slice error cases with literal values, including wrong arity."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_slice_insert(collection, test):
    """Test $slice error cases with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
