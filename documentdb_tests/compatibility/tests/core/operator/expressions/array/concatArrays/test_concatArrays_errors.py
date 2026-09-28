"""
Error tests for $concatArrays expression.

Tests non-array input (all BSON types, special numeric values, boundary values,
string edge cases). $concatArrays propagates null but errors on non-array,
non-null input.
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
from documentdb_tests.framework.error_codes import CONCAT_ARRAYS_NOT_ARRAY_ERROR
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

# Property [Array Type Strictness]: $concatArrays rejects a non-array argument.
NOT_ARRAY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_input",
        doc={"arr0": "hello", "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject string input",
    ),
    ExpressionTestCase(
        id="int_input",
        doc={"arr0": 42, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject int input",
    ),
    ExpressionTestCase(
        id="negative_int_input",
        doc={"arr0": -42, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject negative int input",
    ),
    ExpressionTestCase(
        id="bool_input",
        doc={"arr0": True, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject bool input",
    ),
    ExpressionTestCase(
        id="object_input",
        doc={"arr0": {"a": 1}, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject object input",
    ),
    ExpressionTestCase(
        id="double_input",
        doc={"arr0": 3.14, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject double input",
    ),
    ExpressionTestCase(
        id="negative_double_input",
        doc={"arr0": -3.14, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject negative double input",
    ),
    ExpressionTestCase(
        id="decimal128_input",
        doc={"arr0": Decimal128("1"), "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject decimal128 input",
    ),
    ExpressionTestCase(
        id="int64_input",
        doc={"arr0": Int64(1), "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject int64 input",
    ),
    ExpressionTestCase(
        id="objectid_input",
        doc={"arr0": ObjectId(), "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject objectid input",
    ),
    ExpressionTestCase(
        id="datetime_input",
        doc={"arr0": datetime(2024, 1, 1, tzinfo=timezone.utc), "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject datetime input",
    ),
    ExpressionTestCase(
        id="binary_input",
        doc={"arr0": Binary(b"x", 0), "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject binary input",
    ),
    ExpressionTestCase(
        id="regex_input",
        doc={"arr0": Regex("x"), "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject regex input",
    ),
    ExpressionTestCase(
        id="maxkey_input",
        doc={"arr0": MaxKey(), "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject maxkey input",
    ),
    ExpressionTestCase(
        id="minkey_input",
        doc={"arr0": MinKey(), "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject minkey input",
    ),
    ExpressionTestCase(
        id="timestamp_input",
        doc={"arr0": Timestamp(0, 0), "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject timestamp input",
    ),
    ExpressionTestCase(
        id="non_array_second_arg",
        doc={"arr0": [1], "arr1": 42},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject non-array in second position",
    ),
    ExpressionTestCase(
        id="non_array_middle_arg",
        doc={"arr0": [1], "arr1": "bad", "arr2": [2]},
        expression={"$concatArrays": ["$arr0", "$arr1", "$arr2"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject non-array in middle position",
    ),
]

# Property [Non-Array Numerics]: $concatArrays rejects special float/Decimal128 arguments.
SPECIAL_NUMERIC_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nan_input",
        doc={"arr0": FLOAT_NAN, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject NaN input",
    ),
    ExpressionTestCase(
        id="inf_input",
        doc={"arr0": FLOAT_INFINITY, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject Infinity input",
    ),
    ExpressionTestCase(
        id="neg_inf_input",
        doc={"arr0": FLOAT_NEGATIVE_INFINITY, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject -Infinity input",
    ),
    ExpressionTestCase(
        id="neg_zero_input",
        doc={"arr0": DOUBLE_NEGATIVE_ZERO, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject negative zero input",
    ),
    ExpressionTestCase(
        id="decimal128_nan_input",
        doc={"arr0": DECIMAL128_NAN, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject Decimal128 NaN input",
    ),
    ExpressionTestCase(
        id="decimal128_inf_input",
        doc={"arr0": DECIMAL128_INFINITY, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject Decimal128 Infinity input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_inf_input",
        doc={"arr0": DECIMAL128_NEGATIVE_INFINITY, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject Decimal128 -Infinity input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_zero_input",
        doc={"arr0": DECIMAL128_NEGATIVE_ZERO, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject Decimal128 -0 input",
    ),
]

# Property [Non-Array Boundaries]: $concatArrays rejects numeric boundary values as arguments.
BOUNDARY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int32_max_input",
        doc={"arr0": INT32_MAX, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject INT32_MAX input",
    ),
    ExpressionTestCase(
        id="int32_min_input",
        doc={"arr0": INT32_MIN, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject INT32_MIN input",
    ),
    ExpressionTestCase(
        id="int64_max_input",
        doc={"arr0": INT64_MAX, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject INT64_MAX input",
    ),
    ExpressionTestCase(
        id="int64_min_input",
        doc={"arr0": INT64_MIN, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject INT64_MIN input",
    ),
    ExpressionTestCase(
        id="decimal128_max_input",
        doc={"arr0": DECIMAL128_MAX, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject DECIMAL128_MAX input",
    ),
    ExpressionTestCase(
        id="decimal128_min_input",
        doc={"arr0": DECIMAL128_MIN, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject DECIMAL128_MIN input",
    ),
]

# Property [Non-Array Strings]: $concatArrays rejects string arguments regardless of content.
STRING_EDGE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="comma_separated_string_input",
        doc={"arr0": "1, 2, 3", "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject comma-separated string",
    ),
    ExpressionTestCase(
        id="json_like_string_input",
        doc={"arr0": "[1, 2, 3]", "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject JSON-like string",
    ),
    ExpressionTestCase(
        id="empty_object_input",
        doc={"arr0": {}, "arr1": [1]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR,
        msg="$concatArrays should reject empty object as arg",
    ),
]

ALL_TESTS = (
    NOT_ARRAY_ERROR_TESTS
    + SPECIAL_NUMERIC_ERROR_TESTS
    + BOUNDARY_ERROR_TESTS
    + STRING_EDGE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_concatArrays_not_array_insert(collection, test):
    """Test $concatArrays error with non-array input from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Array Type Strictness]: $concatArrays rejects an object expression argument.
def test_concatArrays_object_expression_input(collection):
    """Test $concatArrays rejects an object expression that is not an array."""
    result = execute_expression_with_insert(collection, {"$concatArrays": [{"a": "$x"}]}, {"x": 1})
    assert_expression_result(result, error_code=CONCAT_ARRAYS_NOT_ARRAY_ERROR)
