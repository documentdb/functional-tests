"""
Error tests for $indexOfArray expression.

Tests non-array first argument, non-integral start/end, negative start/end,
boundary values, negative zero, and wrong arity errors.
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
    EXPRESSION_ARITY_ERROR,
    INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
    INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
    INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_MAX,
    MISSING,
)

# Error: INT64_MAX start/end index (not representable as int32)
BOUNDARY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "start_int64_max",
        doc={"arr": [1, 2, 3], "search": 1, "start": INT64_MAX},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject INT64_MAX start",
    ),
    ExpressionTestCase(
        "end_int64_max",
        doc={"arr": [1, 2, 3], "search": 2, "start": 0, "end": INT64_MAX},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject INT64_MAX end",
    ),
]

# Error: first argument not an array (and not null)
NOT_ARRAY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_as_array",
        doc={"arr": "hello", "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject string as array",
    ),
    ExpressionTestCase(
        "int_as_array",
        doc={"arr": 42, "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject int as array",
    ),
    ExpressionTestCase(
        "double_as_array",
        doc={"arr": 3.14, "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject double as array",
    ),
    ExpressionTestCase(
        "bool_true_as_array",
        doc={"arr": True, "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject bool true as array",
    ),
    ExpressionTestCase(
        "bool_false_as_array",
        doc={"arr": False, "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject bool false as array",
    ),
    ExpressionTestCase(
        "object_as_array",
        doc={"arr": {"a": 1}, "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject object as array",
    ),
    ExpressionTestCase(
        "decimal128_as_array",
        doc={"arr": Decimal128("1"), "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject decimal128 as array",
    ),
    ExpressionTestCase(
        "int64_as_array",
        doc={"arr": Int64(1), "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject int64 as array",
    ),
    ExpressionTestCase(
        "binary_as_array",
        doc={"arr": Binary(b"x", 0), "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject binary as array",
    ),
    ExpressionTestCase(
        "datetime_as_array",
        doc={"arr": datetime(2024, 1, 1, tzinfo=timezone.utc), "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject datetime as array",
    ),
    ExpressionTestCase(
        "objectid_as_array",
        doc={"arr": ObjectId(), "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject objectid as array",
    ),
    ExpressionTestCase(
        "regex_as_array",
        doc={"arr": Regex("x"), "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject regex as array",
    ),
    ExpressionTestCase(
        "maxkey_as_array",
        doc={"arr": MaxKey(), "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject maxkey as array",
    ),
    ExpressionTestCase(
        "minkey_as_array",
        doc={"arr": MinKey(), "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject minkey as array",
    ),
    ExpressionTestCase(
        "timestamp_as_array",
        doc={"arr": Timestamp(0, 0), "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject timestamp as array",
    ),
]

# Error: start index not integral
START_NOT_INTEGRAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "start_fractional_double",
        doc={"arr": [1, 2, 3], "search": 1, "start": 1.5},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject fractional double start",
    ),
    ExpressionTestCase(
        "start_fractional_decimal128",
        doc={"arr": [1, 2, 3], "search": 1, "start": DECIMAL128_HALF},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject fractional decimal128 start",
    ),
    ExpressionTestCase(
        "start_nan",
        doc={"arr": [1, 2, 3], "search": 1, "start": FLOAT_NAN},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject NaN start",
    ),
    ExpressionTestCase(
        "start_inf",
        doc={"arr": [1, 2, 3], "search": 1, "start": FLOAT_INFINITY},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject infinity start",
    ),
    ExpressionTestCase(
        "start_neg_inf",
        doc={"arr": [1, 2, 3], "search": 1, "start": FLOAT_NEGATIVE_INFINITY},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject -infinity start",
    ),
    ExpressionTestCase(
        "start_decimal128_nan",
        doc={"arr": [1, 2, 3], "search": 1, "start": DECIMAL128_NAN},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject decimal128 NaN start",
    ),
    ExpressionTestCase(
        "start_decimal128_inf",
        doc={"arr": [1, 2, 3], "search": 1, "start": DECIMAL128_INFINITY},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject decimal128 infinity start",
    ),
    ExpressionTestCase(
        "start_string",
        doc={"arr": [1, 2, 3], "search": 1, "start": "0"},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject string start",
    ),
    ExpressionTestCase(
        "start_bool",
        doc={"arr": [1, 2, 3], "search": 1, "start": True},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject bool start",
    ),
    ExpressionTestCase(
        "start_array",
        doc={"arr": [1, 2, 3], "search": 1, "start": [0]},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject array start",
    ),
    ExpressionTestCase(
        "start_object",
        doc={"arr": [1, 2, 3], "search": 1, "start": {"a": 0}},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject object start",
    ),
]

# Error: end index not integral
END_NOT_INTEGRAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "end_fractional_double",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": 1.5},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject fractional double end",
    ),
    ExpressionTestCase(
        "end_fractional_decimal128",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": DECIMAL128_HALF},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject fractional decimal128 end",
    ),
    ExpressionTestCase(
        "end_nan",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": FLOAT_NAN},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject NaN end",
    ),
    ExpressionTestCase(
        "end_inf",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": FLOAT_INFINITY},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject infinity end",
    ),
    ExpressionTestCase(
        "end_string",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": "3"},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject string end",
    ),
    ExpressionTestCase(
        "end_bool",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": True},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject bool end",
    ),
    ExpressionTestCase(
        "end_neg_inf",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": FLOAT_NEGATIVE_INFINITY},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject -infinity end",
    ),
    ExpressionTestCase(
        "end_decimal128_nan",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": DECIMAL128_NAN},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject decimal128 NaN end",
    ),
    ExpressionTestCase(
        "end_decimal128_inf",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": DECIMAL128_INFINITY},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject decimal128 infinity end",
    ),
    ExpressionTestCase(
        "end_array",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": [3]},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject array end",
    ),
    ExpressionTestCase(
        "end_object",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": {"a": 0}},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject object end",
    ),
]

# Error: negative start index
START_NEGATIVE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "start_neg_one",
        doc={"arr": [1, 2, 3], "search": 1, "start": -1},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="$indexOfArray should reject negative start -1",
    ),
    ExpressionTestCase(
        "start_neg_large",
        doc={"arr": [1, 2, 3], "search": 1, "start": -100},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="$indexOfArray should reject negative start -100",
    ),
    ExpressionTestCase(
        "start_neg_int64",
        doc={"arr": [1, 2, 3], "search": 1, "start": Int64(-1)},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="$indexOfArray should reject negative Int64 start",
    ),
    ExpressionTestCase(
        "start_neg_double",
        doc={"arr": [1, 2, 3], "search": 1, "start": -1.0},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="$indexOfArray should reject negative double start",
    ),
    ExpressionTestCase(
        "start_neg_decimal128",
        doc={"arr": [1, 2, 3], "search": 1, "start": Decimal128("-1")},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="$indexOfArray should reject negative decimal128 start",
    ),
]

# Error: negative end index
END_NEGATIVE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "end_neg_one",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": -1},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="$indexOfArray should reject negative end -1",
    ),
    ExpressionTestCase(
        "end_neg_large",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": -100},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="$indexOfArray should reject negative end -100",
    ),
    ExpressionTestCase(
        "end_neg_int64",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": Int64(-1)},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="$indexOfArray should reject negative Int64 end",
    ),
    ExpressionTestCase(
        "end_neg_double",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": -1.0},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="$indexOfArray should reject negative double end",
    ),
    ExpressionTestCase(
        "end_neg_decimal128",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": Decimal128("-1")},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="$indexOfArray should reject negative decimal128 end",
    ),
]

# Aggregate and test
ALL_TESTS = (
    BOUNDARY_ERROR_TESTS
    + NOT_ARRAY_ERROR_TESTS
    + START_NOT_INTEGRAL_TESTS
    + END_NOT_INTEGRAL_TESTS
    + START_NEGATIVE_TESTS
    + END_NEGATIVE_TESTS
)

# Property [Literal Evaluation]: error cases with inline literal values.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_as_array",
        expression={"$indexOfArray": ["hello", 1]},
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="$indexOfArray should reject string as array",
    ),
    ExpressionTestCase(
        "start_fractional_double",
        expression={"$indexOfArray": [[1, 2, 3], 1, 1.5]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject fractional double start",
    ),
    ExpressionTestCase(
        "start_neg_one",
        expression={"$indexOfArray": [[1, 2, 3], 1, -1]},
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="$indexOfArray should reject negative start -1",
    ),
    ExpressionTestCase(
        "start_missing_field",
        expression={"$indexOfArray": [[1, 2, 3], 1, MISSING]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject missing field as start",
    ),
    ExpressionTestCase(
        "end_missing_field",
        expression={"$indexOfArray": [[1, 2, 3], 1, 0, MISSING]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject missing field as end",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_indexOfArray_literal(collection, test):
    """Test $indexOfArray error cases with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_indexOfArray_insert(collection, test):
    """Test $indexOfArray error cases with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Arity]: $indexOfArray requires two to four arguments.
ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_args",
        expression={"$indexOfArray": []},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfArray should reject zero arguments",
    ),
    ExpressionTestCase(
        "one_arg",
        expression={"$indexOfArray": [[1, 2, 3]]},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfArray should reject one argument",
    ),
    ExpressionTestCase(
        "five_args",
        expression={"$indexOfArray": [[1, 2, 3], 1, 0, 3, 99]},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfArray should reject five arguments",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARITY_ERROR_TESTS))
def test_indexOfArray_arity_error(collection, test):
    """Test $indexOfArray arity error cases."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Null Index]: $indexOfArray rejects null as start or end index.
NULL_INDEX_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_end",
        expression={"$indexOfArray": [[1, 2, 3], 1, 0, None]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject null end",
    ),
    ExpressionTestCase(
        "null_start",
        expression={"$indexOfArray": [[1, 2, 3], 1, None]},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="$indexOfArray should reject null start",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_INDEX_ERROR_TESTS))
def test_indexOfArray_null_index_error(collection, test):
    """Test $indexOfArray rejects null as start or end index."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
