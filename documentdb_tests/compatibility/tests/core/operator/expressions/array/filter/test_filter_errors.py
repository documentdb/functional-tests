"""
Error tests for $filter expression.

Tests non-array input (all BSON types, special numeric values, boundary values)
and limit parameter validation.
Note: $filter propagates null — null input returns null (tested in core_behavior).
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FILTER_INPUT_NOT_ARRAY_ERROR,
    FILTER_LIMIT_NOT_INTEGRAL_ERROR,
    FILTER_LIMIT_NOT_POSITIVE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Error: non-array input — standard BSON types
NOT_ARRAY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": "hello"},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject string input",
    ),
    ExpressionTestCase(
        "int_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": 42},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject int input",
    ),
    ExpressionTestCase(
        "negative_int_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": -42},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject negative int input",
    ),
    ExpressionTestCase(
        "bool_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": True},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject bool input",
    ),
    ExpressionTestCase(
        "bool_false_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": False},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject bool false input",
    ),
    ExpressionTestCase(
        "object_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": {"a": 1}},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject object input",
    ),
    ExpressionTestCase(
        "double_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": 3.14},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject double input",
    ),
    ExpressionTestCase(
        "negative_double_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": -3.14},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject negative double input",
    ),
    ExpressionTestCase(
        "decimal128_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": Decimal128("1")},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject decimal128 input",
    ),
    ExpressionTestCase(
        "int64_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": Int64(1)},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject int64 input",
    ),
    ExpressionTestCase(
        "objectid_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": ObjectId()},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject objectid input",
    ),
    ExpressionTestCase(
        "datetime_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject datetime input",
    ),
    ExpressionTestCase(
        "binary_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": Binary(b"x", 0)},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject binary input",
    ),
    ExpressionTestCase(
        "regex_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": Regex("x")},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject regex input",
    ),
    ExpressionTestCase(
        "maxkey_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": MaxKey()},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject maxkey input",
    ),
    ExpressionTestCase(
        "minkey_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": MinKey()},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject minkey input",
    ),
    ExpressionTestCase(
        "timestamp_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": Timestamp(0, 0)},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject timestamp input",
    ),
]

# Error: special float/Decimal128 values
SPECIAL_NUMERIC_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": FLOAT_NAN},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject NaN input",
    ),
    ExpressionTestCase(
        "inf_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": FLOAT_INFINITY},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject Infinity input",
    ),
    ExpressionTestCase(
        "neg_inf_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": FLOAT_NEGATIVE_INFINITY},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject -Infinity input",
    ),
    ExpressionTestCase(
        "neg_zero_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DOUBLE_NEGATIVE_ZERO},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject negative zero input",
    ),
    ExpressionTestCase(
        "decimal128_nan_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DECIMAL128_NAN},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject Decimal128 NaN input",
    ),
    ExpressionTestCase(
        "decimal128_neg_nan_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DECIMAL128_NEGATIVE_NAN},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject Decimal128 -NaN input",
    ),
    ExpressionTestCase(
        "decimal128_inf_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DECIMAL128_INFINITY},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject Decimal128 Infinity input",
    ),
    ExpressionTestCase(
        "decimal128_neg_inf_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DECIMAL128_NEGATIVE_INFINITY},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject Decimal128 -Infinity input",
    ),
    ExpressionTestCase(
        "decimal128_neg_zero_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DECIMAL128_NEGATIVE_ZERO},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject Decimal128 -0 input",
    ),
]

# Error: numeric boundary values
BOUNDARY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": INT32_MAX},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject INT32_MAX input",
    ),
    ExpressionTestCase(
        "int32_min_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": INT32_MIN},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject INT32_MIN input",
    ),
    ExpressionTestCase(
        "int64_max_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": INT64_MAX},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject INT64_MAX input",
    ),
    ExpressionTestCase(
        "int64_min_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": INT64_MIN},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject INT64_MIN input",
    ),
    ExpressionTestCase(
        "decimal128_max_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DECIMAL128_MAX},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject DECIMAL128_MAX input",
    ),
    ExpressionTestCase(
        "decimal128_min_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DECIMAL128_MIN},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="$filter should reject DECIMAL128_MIN input",
    ),
]

# Error: invalid limit types
INVALID_LIMIT_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": "1"}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="$filter string limit should error",
    ),
    ExpressionTestCase(
        "bool_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": True}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="$filter bool limit should error",
    ),
    ExpressionTestCase(
        "object_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": {"a": 1}}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="$filter object limit should error",
    ),
    ExpressionTestCase(
        "array_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": [1]}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="$filter array limit should error",
    ),
]

# Error: invalid limit numeric values
INVALID_LIMIT_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": 0}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="$filter limit 0 should error",
    ),
    ExpressionTestCase(
        "neg_int_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": -1}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="$filter negative int should error",
    ),
    ExpressionTestCase(
        "neg_long_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": Int64(-1)}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="$filter negative long should error",
    ),
    ExpressionTestCase(
        "neg_double_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": -1.0}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="$filter negative double should error",
    ),
    ExpressionTestCase(
        "neg_decimal128_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": Decimal128("-1")}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="$filter negative decimal128 should error",
    ),
    ExpressionTestCase(
        "fractional_1_5_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": 1.5}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="$filter fractional 1.5 should error",
    ),
    ExpressionTestCase(
        "fractional_dec_0_5_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": DECIMAL128_HALF}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="$filter fractional decimal128 0.5 should error",
    ),
    ExpressionTestCase(
        "nan_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": FLOAT_NAN}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="$filter naN should error",
    ),
    ExpressionTestCase(
        "inf_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": FLOAT_INFINITY}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="$filter infinity should error",
    ),
    ExpressionTestCase(
        "neg_inf_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": FLOAT_NEGATIVE_INFINITY}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="$filter -Infinity should error",
    ),
    ExpressionTestCase(
        "decimal128_nan_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": DECIMAL128_NAN}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="$filter decimal128 NaN should error",
    ),
    ExpressionTestCase(
        "decimal128_inf_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": DECIMAL128_INFINITY}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="$filter decimal128 Infinity should error",
    ),
    ExpressionTestCase(
        "neg_zero_double_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": DOUBLE_NEGATIVE_ZERO}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="$filter -0.0 limit should error",
    ),
    ExpressionTestCase(
        "neg_zero_decimal128_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": DECIMAL128_NEGATIVE_ZERO}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="$filter decimal128 -0 limit should error",
    ),
]

# Error: cond evaluation errors
COND_EVALUATION_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "cond_divide_by_zero",
        expression={"$filter": {"input": "$arr", "cond": {"$divide": [1, 0]}}},
        doc={"arr": [1, 2]},
        error_code=BAD_VALUE_ERROR,
        msg="$filter division by zero in cond should error",
    ),
]

# Aggregate and test
ALL_TESTS = (
    NOT_ARRAY_ERROR_TESTS
    + SPECIAL_NUMERIC_ERROR_TESTS
    + BOUNDARY_ERROR_TESTS
    + INVALID_LIMIT_TYPE_TESTS
    + INVALID_LIMIT_NUMERIC_TESTS
    + COND_EVALUATION_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_filter_error_insert(collection, test):
    """Test $filter error with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
