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

# Property [Non-Array Element]: $zip rejects non-array elements in inputs with all BSON types.
NOT_ARRAY_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_input",
        doc={"arr0": "hello", "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject string input element",
    ),
    ExpressionTestCase(
        "int_input",
        doc={"arr0": 42, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject int input element",
    ),
    ExpressionTestCase(
        "negative_int_input",
        doc={"arr0": -42, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject negative int input element",
    ),
    ExpressionTestCase(
        "bool_input",
        doc={"arr0": True, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject bool input element",
    ),
    ExpressionTestCase(
        "object_input",
        doc={"arr0": {"a": 1}, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject object input element",
    ),
    ExpressionTestCase(
        "double_input",
        doc={"arr0": 3.14, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject double input element",
    ),
    ExpressionTestCase(
        "negative_double_input",
        doc={"arr0": -3.14, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject negative double input element",
    ),
    ExpressionTestCase(
        "decimal128_input",
        doc={"arr0": Decimal128("1"), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject decimal128 input element",
    ),
    ExpressionTestCase(
        "int64_input",
        doc={"arr0": Int64(1), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject int64 input element",
    ),
    ExpressionTestCase(
        "objectid_input",
        doc={"arr0": ObjectId(), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject objectid input element",
    ),
    ExpressionTestCase(
        "datetime_input",
        doc={"arr0": datetime(2024, 1, 1, tzinfo=timezone.utc), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject datetime input element",
    ),
    ExpressionTestCase(
        "binary_input",
        doc={"arr0": Binary(b"x", 0), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject binary input element",
    ),
    ExpressionTestCase(
        "regex_input",
        doc={"arr0": Regex("x"), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject regex input element",
    ),
    ExpressionTestCase(
        "maxkey_input",
        doc={"arr0": MaxKey(), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject maxkey input element",
    ),
    ExpressionTestCase(
        "minkey_input",
        doc={"arr0": MinKey(), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject minkey input element",
    ),
    ExpressionTestCase(
        "timestamp_input",
        doc={"arr0": Timestamp(0, 0), "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject timestamp input element",
    ),
    ExpressionTestCase(
        "non_array_second_position",
        doc={"arr0": [1], "arr1": 42},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject non-array in second position",
    ),
    ExpressionTestCase(
        "non_array_middle_position",
        doc={"arr0": [1], "arr1": "bad", "arr2": [2]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject non-array in middle position",
    ),
]

# Property [Special Numeric Input]: $map rejects special numeric values as input. as input element
SPECIAL_NUMERIC_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_input",
        doc={"arr0": FLOAT_NAN, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject NaN input element",
    ),
    ExpressionTestCase(
        "inf_input",
        doc={"arr0": FLOAT_INFINITY, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject Infinity input element",
    ),
    ExpressionTestCase(
        "neg_inf_input",
        doc={"arr0": FLOAT_NEGATIVE_INFINITY, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject -Infinity input element",
    ),
    ExpressionTestCase(
        "neg_zero_input",
        doc={"arr0": DOUBLE_NEGATIVE_ZERO, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject negative zero input element",
    ),
    ExpressionTestCase(
        "decimal128_nan_input",
        doc={"arr0": DECIMAL128_NAN, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject Decimal128 NaN input element",
    ),
    ExpressionTestCase(
        "decimal128_inf_input",
        doc={"arr0": DECIMAL128_INFINITY, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject Decimal128 Infinity input element",
    ),
    ExpressionTestCase(
        "decimal128_neg_inf_input",
        doc={"arr0": DECIMAL128_NEGATIVE_INFINITY, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject Decimal128 -Infinity input element",
    ),
    ExpressionTestCase(
        "decimal128_neg_zero_input",
        doc={"arr0": DECIMAL128_NEGATIVE_ZERO, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject Decimal128 -0 input element",
    ),
]

# Property [Boundary Input]: $map rejects numeric boundary values as input. as input element
BOUNDARY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max_input",
        doc={"arr0": INT32_MAX, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject INT32_MAX input element",
    ),
    ExpressionTestCase(
        "int32_min_input",
        doc={"arr0": INT32_MIN, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject INT32_MIN input element",
    ),
    ExpressionTestCase(
        "int64_max_input",
        doc={"arr0": INT64_MAX, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject INT64_MAX input element",
    ),
    ExpressionTestCase(
        "int64_min_input",
        doc={"arr0": INT64_MIN, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject INT64_MIN input element",
    ),
    ExpressionTestCase(
        "decimal128_max_input",
        doc={"arr0": DECIMAL128_MAX, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject DECIMAL128_MAX input element",
    ),
    ExpressionTestCase(
        "decimal128_min_input",
        doc={"arr0": DECIMAL128_MIN, "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject DECIMAL128_MIN input element",
    ),
]

# Property [String Element]: $zip rejects string values as input elements.
STRING_EDGE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "comma_separated_string_input",
        doc={"arr0": "1, 2, 3", "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject comma-separated string",
    ),
    ExpressionTestCase(
        "json_like_string_input",
        doc={"arr0": "[1, 2, 3]", "arr1": [1]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        error_code=ZIP_REQUIRES_ARRAY_ELEMENT_ERROR,
        msg="$zip should reject JSON-like string",
    ),
]

# Property [Invalid useLongestLength]: $zip rejects invalid useLongestLength values.
USE_LONGEST_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "use_longest_string",
        doc={"arr0": [1], "arr1": [2]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": "true"}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="$zip should reject string useLongestLength",
    ),
    ExpressionTestCase(
        "use_longest_int",
        doc={"arr0": [1], "arr1": [2]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": 1}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="$zip should reject int useLongestLength",
    ),
    ExpressionTestCase(
        "use_longest_int_0",
        doc={"arr0": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": 0}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="$zip int 0 should error (not bool)",
    ),
    ExpressionTestCase(
        "use_longest_empty_string",
        doc={"arr0": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": ""}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="$zip empty string should error (not bool)",
    ),
    ExpressionTestCase(
        "use_longest_array",
        doc={"arr0": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": []}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="$zip empty array should error (not bool)",
    ),
    ExpressionTestCase(
        "use_longest_object",
        doc={"arr0": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": {"a": 1}}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="$zip object should error (not bool)",
    ),
    ExpressionTestCase(
        "use_longest_nan",
        doc={"arr0": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": float("nan")}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="$zip naN should error (not bool)",
    ),
    ExpressionTestCase(
        "use_longest_infinity",
        doc={"arr0": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": float("inf")}},
        error_code=ZIP_USE_LONGEST_NOT_BOOL_ERROR,
        msg="$zip infinity should error (not bool)",
    ),
]

# Property [Invalid Defaults]: $zip rejects invalid defaults values.
DEFAULTS_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "defaults_without_use_longest",
        doc={"arr0": [1, 2], "arr1": [3]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "defaults": [0, 0]}},
        error_code=ZIP_DEFAULTS_WITHOUT_LONGEST_ERROR,
        msg="$zip should reject defaults without useLongestLength",
    ),
    ExpressionTestCase(
        "defaults_without_longest_false",
        doc={"arr0": [1], "arr1": [2]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": False, "defaults": [0, 0]}
        },
        error_code=ZIP_DEFAULTS_WITHOUT_LONGEST_ERROR,
        msg="$zip defaults with useLongestLength false should error",
    ),
    ExpressionTestCase(
        "defaults_length_mismatch",
        doc={"arr0": [1, 2], "arr1": [3]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": [0]}
        },
        error_code=ZIP_DEFAULTS_LENGTH_MISMATCH_ERROR,
        msg="$zip should reject defaults with wrong length",
    ),
    ExpressionTestCase(
        "defaults_too_many",
        doc={"arr0": [1], "arr1": [2]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": [0, 0, 0]}
        },
        error_code=ZIP_DEFAULTS_LENGTH_MISMATCH_ERROR,
        msg="$zip should reject defaults longer than inputs",
    ),
    ExpressionTestCase(
        "defaults_not_array",
        doc={"arr0": [1], "arr1": [2]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": "bad"}
        },
        error_code=ZIP_DEFAULTS_NOT_ARRAY_ERROR,
        msg="$zip should reject non-array defaults",
    ),
    ExpressionTestCase(
        "defaults_not_array_object",
        doc={"arr0": [1]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": True, "defaults": {"a": 1}}},
        error_code=ZIP_DEFAULTS_NOT_ARRAY_ERROR,
        msg="$zip defaults as object should error",
    ),
    ExpressionTestCase(
        "defaults_not_array_int",
        doc={"arr0": [1]},
        expression={"$zip": {"inputs": ["$arr0"], "useLongestLength": True, "defaults": 1}},
        error_code=ZIP_DEFAULTS_NOT_ARRAY_ERROR,
        msg="$zip defaults as int should error",
    ),
]

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
