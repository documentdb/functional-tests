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
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
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
        id="string_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": "hello"},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject string input",
    ),
    ExpressionTestCase(
        id="int_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": 42},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject int input",
    ),
    ExpressionTestCase(
        id="negative_int_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": -42},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject negative int input",
    ),
    ExpressionTestCase(
        id="bool_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": True},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject bool input",
    ),
    ExpressionTestCase(
        id="bool_false_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": False},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject bool false input",
    ),
    ExpressionTestCase(
        id="object_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": {"a": 1}},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject object input",
    ),
    ExpressionTestCase(
        id="double_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": 3.14},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject double input",
    ),
    ExpressionTestCase(
        id="negative_double_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": -3.14},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject negative double input",
    ),
    ExpressionTestCase(
        id="decimal128_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": Decimal128("1")},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject decimal128 input",
    ),
    ExpressionTestCase(
        id="int64_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": Int64(1)},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject int64 input",
    ),
    ExpressionTestCase(
        id="objectid_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": ObjectId()},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject objectid input",
    ),
    ExpressionTestCase(
        id="datetime_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject datetime input",
    ),
    ExpressionTestCase(
        id="binary_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": Binary(b"x", 0)},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject binary input",
    ),
    ExpressionTestCase(
        id="regex_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": Regex("x")},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject regex input",
    ),
    ExpressionTestCase(
        id="maxkey_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": MaxKey()},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject maxkey input",
    ),
    ExpressionTestCase(
        id="minkey_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": MinKey()},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject minkey input",
    ),
    ExpressionTestCase(
        id="timestamp_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": Timestamp(0, 0)},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject timestamp input",
    ),
]

# Error: special float/Decimal128 values
SPECIAL_NUMERIC_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nan_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": FLOAT_NAN},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject NaN input",
    ),
    ExpressionTestCase(
        id="inf_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": FLOAT_INFINITY},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Infinity input",
    ),
    ExpressionTestCase(
        id="neg_inf_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": FLOAT_NEGATIVE_INFINITY},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject -Infinity input",
    ),
    ExpressionTestCase(
        id="neg_zero_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DOUBLE_NEGATIVE_ZERO},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject negative zero input",
    ),
    ExpressionTestCase(
        id="decimal128_nan_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DECIMAL128_NAN},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 NaN input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_nan_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": Decimal128("-NaN")},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -NaN input",
    ),
    ExpressionTestCase(
        id="decimal128_inf_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DECIMAL128_INFINITY},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 Infinity input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_inf_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DECIMAL128_NEGATIVE_INFINITY},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -Infinity input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_zero_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DECIMAL128_NEGATIVE_ZERO},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -0 input",
    ),
]

# Error: numeric boundary values
BOUNDARY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int32_max_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": INT32_MAX},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject INT32_MAX input",
    ),
    ExpressionTestCase(
        id="int32_min_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": INT32_MIN},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject INT32_MIN input",
    ),
    ExpressionTestCase(
        id="int64_max_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": INT64_MAX},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject INT64_MAX input",
    ),
    ExpressionTestCase(
        id="int64_min_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": INT64_MIN},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject INT64_MIN input",
    ),
    ExpressionTestCase(
        id="decimal128_max_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DECIMAL128_MAX},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject DECIMAL128_MAX input",
    ),
    ExpressionTestCase(
        id="decimal128_min_input",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": DECIMAL128_MIN},
        error_code=FILTER_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject DECIMAL128_MIN input",
    ),
]

# Error: invalid limit types
INVALID_LIMIT_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": "1"}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="String limit should error",
    ),
    ExpressionTestCase(
        id="bool_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": True}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="Bool limit should error",
    ),
    ExpressionTestCase(
        id="object_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": {"a": 1}}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="Object limit should error",
    ),
    ExpressionTestCase(
        id="array_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": [1]}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="Array limit should error",
    ),
]

# Error: invalid limit numeric values
INVALID_LIMIT_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="zero_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": 0}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="limit 0 should error",
    ),
    ExpressionTestCase(
        id="neg_int_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": -1}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="Negative int should error",
    ),
    ExpressionTestCase(
        id="neg_long_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": Int64(-1)}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="Negative long should error",
    ),
    ExpressionTestCase(
        id="neg_double_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": -1.0}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="Negative double should error",
    ),
    ExpressionTestCase(
        id="neg_decimal128_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": Decimal128("-1")}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="Negative decimal128 should error",
    ),
    ExpressionTestCase(
        id="fractional_1_5_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": 1.5}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="Fractional 1.5 should error",
    ),
    ExpressionTestCase(
        id="fractional_dec_0_5_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": Decimal128("0.5")}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="Fractional decimal128 0.5 should error",
    ),
    ExpressionTestCase(
        id="nan_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": float("nan")}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="NaN should error",
    ),
    ExpressionTestCase(
        id="inf_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": float("inf")}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="Infinity should error",
    ),
    ExpressionTestCase(
        id="neg_inf_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": float("-inf")}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="-Infinity should error",
    ),
    ExpressionTestCase(
        id="decimal128_nan_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": Decimal128("NaN")}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="Decimal128 NaN should error",
    ),
    ExpressionTestCase(
        id="decimal128_inf_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": Decimal128("Infinity")}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_INTEGRAL_ERROR,
        msg="Decimal128 Infinity should error",
    ),
    ExpressionTestCase(
        id="neg_zero_double_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": -0.0}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="-0.0 limit should error",
    ),
    ExpressionTestCase(
        id="neg_zero_decimal128_limit",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": Decimal128("-0")}},
        doc={"arr": [1, 2, 3]},
        error_code=FILTER_LIMIT_NOT_POSITIVE_ERROR,
        msg="Decimal128 -0 limit should error",
    ),
]

# Error: cond evaluation errors
COND_EVALUATION_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="cond_divide_by_zero",
        expression={"$filter": {"input": "$arr", "cond": {"$divide": [1, 0]}}},
        doc={"arr": [1, 2]},
        error_code=BAD_VALUE_ERROR,
        msg="Division by zero in cond should error",
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
