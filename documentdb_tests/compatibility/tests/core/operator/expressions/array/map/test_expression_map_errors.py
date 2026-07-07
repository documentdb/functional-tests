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

# ---------------------------------------------------------------------------
# Error: non-array input — standard BSON types
# ---------------------------------------------------------------------------
NOT_ARRAY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": "hello"},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject string input",
    ),
    ExpressionTestCase(
        id="int_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": 42},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject int input",
    ),
    ExpressionTestCase(
        id="negative_int_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": -42},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject negative int input",
    ),
    ExpressionTestCase(
        id="bool_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": True},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject bool input",
    ),
    ExpressionTestCase(
        id="object_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": {"a": 1}},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject object input",
    ),
    ExpressionTestCase(
        id="double_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": 3.14},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject double input",
    ),
    ExpressionTestCase(
        id="negative_double_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": -3.14},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject negative double input",
    ),
    ExpressionTestCase(
        id="decimal128_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": Decimal128("1")},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject decimal128 input",
    ),
    ExpressionTestCase(
        id="int64_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": Int64(1)},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject int64 input",
    ),
    ExpressionTestCase(
        id="objectid_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": ObjectId()},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject objectid input",
    ),
    ExpressionTestCase(
        id="datetime_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject datetime input",
    ),
    ExpressionTestCase(
        id="binary_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": Binary(b"x", 0)},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject binary input",
    ),
    ExpressionTestCase(
        id="regex_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": Regex("x")},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject regex input",
    ),
    ExpressionTestCase(
        id="maxkey_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": MaxKey()},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject maxkey input",
    ),
    ExpressionTestCase(
        id="minkey_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": MinKey()},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject minkey input",
    ),
    ExpressionTestCase(
        id="timestamp_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": Timestamp(0, 0)},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject timestamp input",
    ),
]

# ---------------------------------------------------------------------------
# Error: special float/Decimal128 values
# ---------------------------------------------------------------------------
SPECIAL_NUMERIC_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nan_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": FLOAT_NAN},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject NaN input",
    ),
    ExpressionTestCase(
        id="inf_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": FLOAT_INFINITY},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Infinity input",
    ),
    ExpressionTestCase(
        id="neg_inf_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": FLOAT_NEGATIVE_INFINITY},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject -Infinity input",
    ),
    ExpressionTestCase(
        id="neg_zero_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DOUBLE_NEGATIVE_ZERO},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject negative zero input",
    ),
    ExpressionTestCase(
        id="decimal128_nan_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DECIMAL128_NAN},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 NaN input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_nan_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": Decimal128("-NaN")},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -NaN input",
    ),
    ExpressionTestCase(
        id="decimal128_inf_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DECIMAL128_INFINITY},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 Infinity input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_inf_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DECIMAL128_NEGATIVE_INFINITY},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -Infinity input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_zero_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DECIMAL128_NEGATIVE_ZERO},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -0 input",
    ),
]

# ---------------------------------------------------------------------------
# Error: numeric boundary values
# ---------------------------------------------------------------------------
BOUNDARY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int32_max_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": INT32_MAX},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject INT32_MAX input",
    ),
    ExpressionTestCase(
        id="int32_min_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": INT32_MIN},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject INT32_MIN input",
    ),
    ExpressionTestCase(
        id="int64_max_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": INT64_MAX},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject INT64_MAX input",
    ),
    ExpressionTestCase(
        id="int64_min_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": INT64_MIN},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject INT64_MIN input",
    ),
    ExpressionTestCase(
        id="decimal128_max_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DECIMAL128_MAX},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject DECIMAL128_MAX input",
    ),
    ExpressionTestCase(
        id="decimal128_min_input",
        expression={"$map": {"input": "$arr", "in": "$$this"}},
        doc={"arr": DECIMAL128_MIN},
        error_code=MAP_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject DECIMAL128_MIN input",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_TESTS = NOT_ARRAY_ERROR_TESTS + SPECIAL_NUMERIC_ERROR_TESTS + BOUNDARY_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_map_not_array_insert(collection, test):
    """Test $map error with non-array input from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
