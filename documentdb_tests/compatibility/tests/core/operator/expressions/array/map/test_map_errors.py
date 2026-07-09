"""
Error tests for $map expression.

Tests non-array input (all BSON types, special numeric values, boundary values),
structural errors (missing fields, unknown fields).
Note: $map propagates null — null input returns null (tested in core_behavior).
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    MAP_INPUT_NOT_ARRAY_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
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

# Property [Non-Array Input]: $map rejects non-array input with all BSON types.
NOT_ARRAY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": "hello"},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject string input",
    ),
    ExpressionTestCase(
        "int_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": 42},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject int input",
    ),
    ExpressionTestCase(
        "negative_int_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": -42},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject negative int input",
    ),
    ExpressionTestCase(
        "bool_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": True},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject bool input",
    ),
    ExpressionTestCase(
        "object_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": {"a": 1}},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject object input",
    ),
    ExpressionTestCase(
        "double_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": 3.14},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject double input",
    ),
    ExpressionTestCase(
        "negative_double_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": -3.14},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject negative double input",
    ),
    ExpressionTestCase(
        "decimal128_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": Decimal128("1")},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject decimal128 input",
    ),
    ExpressionTestCase(
        "int64_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": Int64(1)},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject int64 input",
    ),
    ExpressionTestCase(
        "objectid_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": ObjectId()},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject objectid input",
    ),
    ExpressionTestCase(
        "datetime_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject datetime input",
    ),
    ExpressionTestCase(
        "binary_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": Binary(b"x", 0)},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject binary input",
    ),
    ExpressionTestCase(
        "regex_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": Regex("x")},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject regex input",
    ),
    ExpressionTestCase(
        "maxkey_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": MaxKey()},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject maxkey input",
    ),
    ExpressionTestCase(
        "minkey_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": MinKey()},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject minkey input",
    ),
    ExpressionTestCase(
        "timestamp_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": Timestamp(0, 0)},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject timestamp input",
    ),
]

# Property [Special Numeric Input]: $map rejects special numeric values as input.
SPECIAL_NUMERIC_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": FLOAT_NAN},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject NaN input",
    ),
    ExpressionTestCase(
        "inf_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": FLOAT_INFINITY},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject Infinity input",
    ),
    ExpressionTestCase(
        "neg_inf_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": FLOAT_NEGATIVE_INFINITY},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject -Infinity input",
    ),
    ExpressionTestCase(
        "neg_zero_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DOUBLE_NEGATIVE_ZERO},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject negative zero input",
    ),
    ExpressionTestCase(
        "decimal128_nan_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DECIMAL128_NAN},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject Decimal128 NaN input",
    ),
    ExpressionTestCase(
        "decimal128_neg_nan_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DECIMAL128_NEGATIVE_NAN},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject Decimal128 -NaN input",
    ),
    ExpressionTestCase(
        "decimal128_inf_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DECIMAL128_INFINITY},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject Decimal128 Infinity input",
    ),
    ExpressionTestCase(
        "decimal128_neg_inf_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DECIMAL128_NEGATIVE_INFINITY},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject Decimal128 -Infinity input",
    ),
    ExpressionTestCase(
        "decimal128_neg_zero_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DECIMAL128_NEGATIVE_ZERO},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject Decimal128 -0 input",
    ),
]

# Property [Boundary Input]: $map rejects numeric boundary values as input.
BOUNDARY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": INT32_MAX},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject INT32_MAX input",
    ),
    ExpressionTestCase(
        "int32_min_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": INT32_MIN},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject INT32_MIN input",
    ),
    ExpressionTestCase(
        "int64_max_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": INT64_MAX},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject INT64_MAX input",
    ),
    ExpressionTestCase(
        "int64_min_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": INT64_MIN},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject INT64_MIN input",
    ),
    ExpressionTestCase(
        "decimal128_max_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DECIMAL128_MAX},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject DECIMAL128_MAX input",
    ),
    ExpressionTestCase(
        "decimal128_min_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DECIMAL128_MIN},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="$map should reject DECIMAL128_MIN input",
    ),
]

ALL_TESTS = NOT_ARRAY_ERROR_TESTS + SPECIAL_NUMERIC_ERROR_TESTS + BOUNDARY_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_map_non_array_input_error(collection, test):
    """Test $map rejects non-array input with correct error code."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
