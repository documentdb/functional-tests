"""
Error tests for $zip expression.

Tests non-array inputs, invalid useLongestLength, invalid defaults,
defaults without useLongestLength, and defaults length mismatch.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    ZIP_DEFAULTS_LENGTH_MISMATCH_ERROR,
    ZIP_DEFAULTS_NOT_ARRAY_ERROR,
    ZIP_DEFAULTS_WITHOUT_LONGEST_ERROR,
    ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
    ZIP_USE_LONGEST_NOT_BOOL_ERROR,
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

# Error: non-array input element — standard BSON types
NOT_ARRAY_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_input",
        doc={"arr0": "hello", "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject string input element",
    ),
    ExpressionTestCase(
        id="int_input",
        doc={"arr0": 42, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject int input element",
    ),
    ExpressionTestCase(
        id="negative_int_input",
        doc={"arr0": -42, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject negative int input element",
    ),
    ExpressionTestCase(
        id="bool_input",
        doc={"arr0": True, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject bool input element",
    ),
    ExpressionTestCase(
        id="object_input",
        doc={"arr0": {"a": 1}, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject object input element",
    ),
    ExpressionTestCase(
        id="double_input",
        doc={"arr0": 3.14, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject double input element",
    ),
    ExpressionTestCase(
        id="negative_double_input",
        doc={"arr0": -3.14, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject negative double input element",
    ),
    ExpressionTestCase(
        id="decimal128_input",
        doc={"arr0": Decimal128("1"), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject decimal128 input element",
    ),
    ExpressionTestCase(
        id="int64_input",
        doc={"arr0": Int64(1), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject int64 input element",
    ),
    ExpressionTestCase(
        id="objectid_input",
        doc={"arr0": ObjectId(), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject objectid input element",
    ),
    ExpressionTestCase(
        id="datetime_input",
        doc={"arr0": datetime(2024, 1, 1, tzinfo=timezone.utc), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject datetime input element",
    ),
    ExpressionTestCase(
        id="binary_input",
        doc={"arr0": Binary(b"x", 0), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject binary input element",
    ),
    ExpressionTestCase(
        id="regex_input",
        doc={"arr0": Regex("x"), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject regex input element",
    ),
    ExpressionTestCase(
        id="maxkey_input",
        doc={"arr0": MaxKey(), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject maxkey input element",
    ),
    ExpressionTestCase(
        id="minkey_input",
        doc={"arr0": MinKey(), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject minkey input element",
    ),
    ExpressionTestCase(
        id="timestamp_input",
        doc={"arr0": Timestamp(0, 0), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject timestamp input element",
    ),
    ExpressionTestCase(
        id="non_array_second_position",
        doc={"arr0": [1], "arr1": 42},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject non-array in second position",
    ),
    ExpressionTestCase(
        id="non_array_middle_position",
        doc={"arr0": [1], "arr1": "bad", "arr2": [2]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject non-array in middle position",
    ),
]

# Error: special float/Decimal128 values as input element
SPECIAL_NUMERIC_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nan_input",
        doc={"arr0": FLOAT_NAN, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject NaN input element",
    ),
    ExpressionTestCase(
        id="inf_input",
        doc={"arr0": FLOAT_INFINITY, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject Infinity input element",
    ),
    ExpressionTestCase(
        id="neg_inf_input",
        doc={"arr0": FLOAT_NEGATIVE_INFINITY, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject -Infinity input element",
    ),
    ExpressionTestCase(
        id="neg_zero_input",
        doc={"arr0": DOUBLE_NEGATIVE_ZERO, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject negative zero input element",
    ),
    ExpressionTestCase(
        id="decimal128_nan_input",
        doc={"arr0": DECIMAL128_NAN, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject Decimal128 NaN input element",
    ),
    ExpressionTestCase(
        id="decimal128_inf_input",
        doc={"arr0": DECIMAL128_INFINITY, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject Decimal128 Infinity input element",
    ),
    ExpressionTestCase(
        id="decimal128_neg_inf_input",
        doc={"arr0": DECIMAL128_NEGATIVE_INFINITY, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject Decimal128 -Infinity input element",
    ),
    ExpressionTestCase(
        id="decimal128_neg_zero_input",
        doc={"arr0": DECIMAL128_NEGATIVE_ZERO, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject Decimal128 -0 input element",
    ),
]

# Error: numeric boundary values as input element
BOUNDARY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int32_max_input",
        doc={"arr0": INT32_MAX, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject INT32_MAX input element",
    ),
    ExpressionTestCase(
        id="int32_min_input",
        doc={"arr0": INT32_MIN, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject INT32_MIN input element",
    ),
    ExpressionTestCase(
        id="int64_max_input",
        doc={"arr0": INT64_MAX, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject INT64_MAX input element",
    ),
    ExpressionTestCase(
        id="int64_min_input",
        doc={"arr0": INT64_MIN, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject INT64_MIN input element",
    ),
    ExpressionTestCase(
        id="decimal128_max_input",
        doc={"arr0": DECIMAL128_MAX, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject DECIMAL128_MAX input element",
    ),
    ExpressionTestCase(
        id="decimal128_min_input",
        doc={"arr0": DECIMAL128_MIN, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject DECIMAL128_MIN input element",
    ),
]

# Error: string edge cases as input element
STRING_EDGE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="comma_separated_string_input",
        doc={"arr0": "1, 2, 3", "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject comma-separated string",
    ),
    ExpressionTestCase(
        id="json_like_string_input",
        doc={"arr0": "[1, 2, 3]", "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="Should reject JSON-like string",
    ),
]

# Error: invalid useLongestLength
USE_LONGEST_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="use_longest_string",
        doc={"arr0": [1], "arr1": [2]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": "true"}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Should reject string useLongestLength",
    ),
    ExpressionTestCase(
        id="use_longest_int",
        doc={"arr0": [1], "arr1": [2]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": 1}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Should reject int useLongestLength",
    ),
    ExpressionTestCase(
        id="use_longest_int_0",
        doc={"arr0": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": 0}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Int 0 should error (not bool)",
    ),
    ExpressionTestCase(
        id="use_longest_empty_string",
        doc={"arr0": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": ""}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Empty string should error (not bool)",
    ),
    ExpressionTestCase(
        id="use_longest_array",
        doc={"arr0": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": []}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Empty array should error (not bool)",
    ),
    ExpressionTestCase(
        id="use_longest_object",
        doc={"arr0": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": {"a": 1}}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Object should error (not bool)",
    ),
    ExpressionTestCase(
        id="use_longest_nan",
        doc={"arr0": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": float("nan")}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="NaN should error (not bool)",
    ),
    ExpressionTestCase(
        id="use_longest_infinity",
        doc={"arr0": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": float("inf")}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="Infinity should error (not bool)",
    ),
]

# Error: invalid defaults
DEFAULTS_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="defaults_without_use_longest",
        doc={"arr0": [1, 2], "arr1": [3]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "defaults": [0, 0]}},
        error_code=ZIP_DEFAULTS_WITHOUT_LONGEST_ERROR,
        msg="Should reject defaults without useLongestLength",
    ),
    ExpressionTestCase(
        id="defaults_without_longest_false",
        doc={"arr0": [1], "arr1": [2]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": False, "defaults": [0, 0]}
        },
        error_code=ZIP_DEFAULTS_WITHOUT_LONGEST_ERROR,
        msg="defaults with useLongestLength false should error",
    ),
    ExpressionTestCase(
        id="defaults_length_mismatch",
        doc={"arr0": [1, 2], "arr1": [3]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": [0]}
        },
        error_code=ZIP_DEFAULTS_LENGTH_MISMATCH_ERROR,
        msg="Should reject defaults with wrong length",
    ),
    ExpressionTestCase(
        id="defaults_too_many",
        doc={"arr0": [1], "arr1": [2]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": [0, 0, 0]}
        },
        error_code=ZIP_DEFAULTS_LENGTH_MISMATCH_ERROR,
        msg="Should reject defaults longer than inputs",
    ),
    ExpressionTestCase(
        id="defaults_not_array",
        doc={"arr0": [1], "arr1": [2]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": "bad"}
        },
        error_code=ZIP_DEFAULTS_NOT_ARRAY_ERROR,
        msg="Should reject non-array defaults",
    ),
    ExpressionTestCase(
        id="defaults_not_array_object",
        doc={"arr0": [1]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": True, "defaults": {"a": 1}}},
        error_code=ZIP_DEFAULTS_NOT_ARRAY_ERROR,
        msg="defaults as object should error",
    ),
    ExpressionTestCase(
        id="defaults_not_array_int",
        doc={"arr0": [1]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": True, "defaults": 1}},
        error_code=ZIP_DEFAULTS_NOT_ARRAY_ERROR,
        msg="defaults as int should error",
    ),
]

# Aggregate and test
ALL_INPUT_ELEMENT_TESTS = (
    NOT_ARRAY_ELEMENT_TESTS
    + SPECIAL_NUMERIC_ERROR_TESTS
    + BOUNDARY_ERROR_TESTS
    + STRING_EDGE_ERROR_TESTS
    + USE_LONGEST_ERROR_TESTS
    + DEFAULTS_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_INPUT_ELEMENT_TESTS))
def test_zip_non_array_input_error(collection, test):
    """Test $zip rejects non-array inputs and invalid useLongestLength/defaults."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
