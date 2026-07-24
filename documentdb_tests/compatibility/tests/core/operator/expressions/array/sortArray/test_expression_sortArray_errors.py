"""
Error tests for $sortArray expression.

Tests non-array input (all BSON types, special numeric values, boundary values,
string edge cases) and argument structure validation. Note: $sortArray
propagates null — null/missing input tests are in
test_expression_sortArray_core_behavior.py.
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
    SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
    SORT_ARRAY_INVALID_SORT_DOC_ERROR,
    SORT_ARRAY_INVALID_SORT_SCALAR_ERROR,
    SORT_ARRAY_INVALID_SORT_TYPE_ERROR,
    SORT_ARRAY_MISSING_INPUT_ERROR,
    SORT_ARRAY_MISSING_SORTBY_ERROR,
    SORT_ARRAY_NON_OBJECT_ARG_ERROR,
    SORT_ARRAY_UNKNOWN_FIELD_ERROR,
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

# Property [Literal-path parity]: representative non-array rejections also
# run through the literal-value path (not just via inserted documents), and
# are appended to ALL_TESTS below so they also get insert coverage.
LITERAL_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_input",
        expression={"$sortArray": {"input": "hello", "sortBy": 1}},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject string input",
    ),
    ExpressionTestCase(
        id="timestamp_input",
        expression={"$sortArray": {"input": Timestamp(0, 0), "sortBy": 1}},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject timestamp input",
    ),
    ExpressionTestCase(
        id="nan_input",
        expression={"$sortArray": {"input": FLOAT_NAN, "sortBy": 1}},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject NaN input",
    ),
    ExpressionTestCase(
        id="int32_max_input",
        expression={"$sortArray": {"input": INT32_MAX, "sortBy": 1}},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject INT32_MAX input",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_ERROR_TESTS))
def test_sortArray_not_array_literal(collection, test):
    """Test $sortArray error with non-array literal input."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Non-array input rejection]: every non-array BSON type (scalar,
# object, and edge values like negative numbers) is rejected with
# SORT_ARRAY_INPUT_NOT_ARRAY_ERROR — no type is silently coerced.
NOT_ARRAY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": "hello"},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject string input",
    ),
    ExpressionTestCase(
        id="int_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": 42},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject int input",
    ),
    ExpressionTestCase(
        id="negative_int_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": -42},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject negative int input",
    ),
    ExpressionTestCase(
        id="bool_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": True},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject bool input",
    ),
    ExpressionTestCase(
        id="object_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": {"a": 1}},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject object input",
    ),
    ExpressionTestCase(
        id="double_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": 3.14},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject double input",
    ),
    ExpressionTestCase(
        id="negative_double_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": -3.14},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject negative double input",
    ),
    ExpressionTestCase(
        id="decimal128_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": Decimal128("1")},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject decimal128 input",
    ),
    ExpressionTestCase(
        id="int64_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": Int64(1)},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject int64 input",
    ),
    ExpressionTestCase(
        id="objectid_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": ObjectId()},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject objectid input",
    ),
    ExpressionTestCase(
        id="datetime_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject datetime input",
    ),
    ExpressionTestCase(
        id="binary_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": Binary(b"x", 0)},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject binary input",
    ),
    ExpressionTestCase(
        id="regex_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": Regex("x")},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject regex input",
    ),
    ExpressionTestCase(
        id="maxkey_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": MaxKey()},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject maxkey input",
    ),
    ExpressionTestCase(
        id="minkey_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": MinKey()},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject minkey input",
    ),
    ExpressionTestCase(
        id="timestamp_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": Timestamp(0, 0)},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject timestamp input",
    ),
]

# Property [Special numeric non-array rejection]: IEEE-754/Decimal128 special
# numeric values (±Infinity, ±0, NaN) are still scalars, not arrays, and are
# rejected the same as any other non-array input.
SPECIAL_NUMERIC_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nan_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": FLOAT_NAN},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject NaN input",
    ),
    ExpressionTestCase(
        id="inf_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": FLOAT_INFINITY},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Infinity input",
    ),
    ExpressionTestCase(
        id="neg_inf_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": FLOAT_NEGATIVE_INFINITY},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject -Infinity input",
    ),
    ExpressionTestCase(
        id="neg_zero_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": DOUBLE_NEGATIVE_ZERO},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject negative zero input",
    ),
    ExpressionTestCase(
        id="decimal128_nan_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": DECIMAL128_NAN},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 NaN input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_nan_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": Decimal128("-NaN")},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -NaN input",
    ),
    ExpressionTestCase(
        id="decimal128_inf_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": DECIMAL128_INFINITY},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 Infinity input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_inf_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": DECIMAL128_NEGATIVE_INFINITY},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -Infinity input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_zero_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": DECIMAL128_NEGATIVE_ZERO},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -0 input",
    ),
]

# Property [Boundary-value non-array rejection]: min/max values for each
# numeric BSON type are rejected the same as any other non-array scalar —
# the not-array check has no numeric-magnitude special-casing at the
# boundaries.
BOUNDARY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int32_max_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": INT32_MAX},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject INT32_MAX input",
    ),
    ExpressionTestCase(
        id="int32_min_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": INT32_MIN},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject INT32_MIN input",
    ),
    ExpressionTestCase(
        id="int64_max_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": INT64_MAX},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject INT64_MAX input",
    ),
    ExpressionTestCase(
        id="int64_min_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": INT64_MIN},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject INT64_MIN input",
    ),
    ExpressionTestCase(
        id="decimal128_max_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": DECIMAL128_MAX},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject DECIMAL128_MAX input",
    ),
    ExpressionTestCase(
        id="decimal128_min_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": DECIMAL128_MIN},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject DECIMAL128_MIN input",
    ),
]

# Property [String-shape non-array rejection]: strings that merely look like
# array syntax (comma-separated or JSON array text) are still the string BSON
# type and are rejected, not parsed or reinterpreted as an array.
STRING_EDGE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="comma_separated_string_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": "1, 2, 3"},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject comma-separated string",
    ),
    ExpressionTestCase(
        id="json_like_string_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1}},
        doc={"arr": "[1, 2, 3]"},
        error_code=SORT_ARRAY_INPUT_NOT_ARRAY_ERROR,
        msg="Should reject JSON-like string",
    ),
]

# Property [Invalid sortBy scalar value]: a scalar sortBy must be exactly 1
# or -1; any other numeric value (0, out-of-range, fractional, or a valid
# numeric type holding an invalid value like Int64(2)/Decimal128("1.5")) is
# rejected with SORT_ARRAY_INVALID_SORT_SCALAR_ERROR.
INVALID_SORTBY_SCALAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="sortby_zero",
        expression={"$sortArray": {"input": "$arr", "sortBy": 0}},
        doc={"arr": [1, 2]},
        error_code=SORT_ARRAY_INVALID_SORT_SCALAR_ERROR,
        msg="sortBy 0 should error",
    ),
    ExpressionTestCase(
        id="sortby_two",
        expression={"$sortArray": {"input": "$arr", "sortBy": 2}},
        doc={"arr": [1, 2]},
        error_code=SORT_ARRAY_INVALID_SORT_SCALAR_ERROR,
        msg="sortBy 2 should error",
    ),
    ExpressionTestCase(
        id="sortby_negative_two",
        expression={"$sortArray": {"input": "$arr", "sortBy": -2}},
        doc={"arr": [1, 2]},
        error_code=SORT_ARRAY_INVALID_SORT_SCALAR_ERROR,
        msg="sortBy -2 (negative out-of-range) should error",
    ),
    ExpressionTestCase(
        id="sortby_fractional",
        expression={"$sortArray": {"input": "$arr", "sortBy": 1.5}},
        doc={"arr": [1, 2]},
        error_code=SORT_ARRAY_INVALID_SORT_SCALAR_ERROR,
        msg="sortBy 1.5 should error",
    ),
    ExpressionTestCase(
        id="sortby_decimal128_fractional",
        expression={"$sortArray": {"input": "$arr", "sortBy": Decimal128("1.5")}},
        doc={"arr": [1, 2]},
        error_code=SORT_ARRAY_INVALID_SORT_SCALAR_ERROR,
        msg="sortBy Decimal128('1.5') should error like the double 1.5 case",
    ),
    ExpressionTestCase(
        id="sortby_int64_two",
        expression={"$sortArray": {"input": "$arr", "sortBy": Int64(2)}},
        doc={"arr": [1, 2]},
        error_code=SORT_ARRAY_INVALID_SORT_SCALAR_ERROR,
        msg="sortBy Int64(2) should error — valid numeric type, invalid value",
    ),
]

# Property [Invalid sortBy type]: sortBy must be a numeric scalar (±1) or a
# field-spec document; any other BSON type (string, null, bool, array) is
# rejected with SORT_ARRAY_INVALID_SORT_TYPE_ERROR.
INVALID_SORTBY_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="sortby_string",
        expression={"$sortArray": {"input": "$arr", "sortBy": "invalid"}},
        doc={"arr": [1, 2]},
        error_code=SORT_ARRAY_INVALID_SORT_TYPE_ERROR,
        msg="sortBy string should error",
    ),
    ExpressionTestCase(
        id="sortby_null",
        expression={"$sortArray": {"input": "$arr", "sortBy": None}},
        doc={"arr": [1, 2]},
        error_code=SORT_ARRAY_INVALID_SORT_TYPE_ERROR,
        msg="sortBy null should error",
    ),
    ExpressionTestCase(
        id="sortby_bool",
        expression={"$sortArray": {"input": "$arr", "sortBy": True}},
        doc={"arr": [1, 2]},
        error_code=SORT_ARRAY_INVALID_SORT_TYPE_ERROR,
        msg="sortBy bool should error",
    ),
    ExpressionTestCase(
        id="sortby_array",
        expression={"$sortArray": {"input": "$arr", "sortBy": [1]}},
        doc={"arr": [1, 2]},
        error_code=SORT_ARRAY_INVALID_SORT_TYPE_ERROR,
        msg="sortBy array should error",
    ),
]

# Property [Invalid sortBy field-spec value]: within a sortBy document, each
# field's direction value must be exactly 1 or -1; any other value (0, 2,
# a string, or an empty document with no fields at all) is rejected with
# SORT_ARRAY_INVALID_SORT_DOC_ERROR.
INVALID_SORTBY_DOC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="sortby_doc_zero",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"a": 0}}},
        doc={"arr": [{"a": 1}]},
        error_code=SORT_ARRAY_INVALID_SORT_DOC_ERROR,
        msg="sortBy {a:0} should error",
    ),
    ExpressionTestCase(
        id="sortby_doc_two",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"a": 2}}},
        doc={"arr": [{"a": 1}]},
        error_code=SORT_ARRAY_INVALID_SORT_DOC_ERROR,
        msg="sortBy {a:2} should error",
    ),
    ExpressionTestCase(
        id="sortby_doc_string",
        expression={"$sortArray": {"input": "$arr", "sortBy": {"a": "asc"}}},
        doc={"arr": [{"a": 1}]},
        error_code=SORT_ARRAY_INVALID_SORT_DOC_ERROR,
        msg="sortBy {a:'asc'} should error",
    ),
    ExpressionTestCase(
        id="sortby_empty_doc",
        expression={"$sortArray": {"input": "$arr", "sortBy": {}}},
        doc={"arr": [{"a": 1}]},
        error_code=SORT_ARRAY_INVALID_SORT_DOC_ERROR,
        msg="sortBy {} should error",
    ),
]

ALL_TESTS = (
    NOT_ARRAY_ERROR_TESTS
    + SPECIAL_NUMERIC_ERROR_TESTS
    + BOUNDARY_ERROR_TESTS
    + STRING_EDGE_ERROR_TESTS
    + INVALID_SORTBY_SCALAR_TESTS
    + INVALID_SORTBY_TYPE_TESTS
    + INVALID_SORTBY_DOC_TESTS
    + LITERAL_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_sortArray_not_array_insert(collection, test):
    """Test $sortArray error with non-array input from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Argument structure validation]: the `$sortArray` argument must be
# a well-formed object with exactly `input` and `sortBy` and no others; a
# missing/unknown field or non-object argument is rejected with its own
# named error.
STRUCTURE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="empty_object",
        expression={"$sortArray": {}},
        error_code=SORT_ARRAY_MISSING_INPUT_ERROR,
        msg="Empty object should error",
    ),
    ExpressionTestCase(
        id="missing_input",
        expression={"$sortArray": {"sortBy": 1}},
        error_code=SORT_ARRAY_MISSING_INPUT_ERROR,
        msg="Missing input should error",
    ),
    ExpressionTestCase(
        id="missing_sortby",
        expression={"$sortArray": {"input": [1, 2, 3]}},
        error_code=SORT_ARRAY_MISSING_SORTBY_ERROR,
        msg="Missing sortBy should error",
    ),
    ExpressionTestCase(
        id="unknown_field",
        expression={"$sortArray": {"input": [1], "sortBy": 1, "extra": 1}},
        error_code=SORT_ARRAY_UNKNOWN_FIELD_ERROR,
        msg="Unknown field should error",
    ),
    ExpressionTestCase(
        id="non_object_arg_array",
        expression={"$sortArray": [[1, 2, 3], 1]},
        error_code=SORT_ARRAY_NON_OBJECT_ARG_ERROR,
        msg="Array argument should error",
    ),
    ExpressionTestCase(
        id="non_object_arg_scalar",
        expression={"$sortArray": 1},
        error_code=SORT_ARRAY_NON_OBJECT_ARG_ERROR,
        msg="Scalar argument should error",
    ),
    ExpressionTestCase(
        id="non_object_arg_string",
        expression={"$sortArray": "hello"},
        error_code=SORT_ARRAY_NON_OBJECT_ARG_ERROR,
        msg="String argument should error",
    ),
    ExpressionTestCase(
        id="non_object_arg_null",
        expression={"$sortArray": None},
        error_code=SORT_ARRAY_NON_OBJECT_ARG_ERROR,
        msg="Null argument should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STRUCTURE_ERROR_TESTS))
def test_sortArray_argument_handling(collection, test):
    """Test $sortArray argument structure validation."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Error precedence] (Rule 18): when multiple argument problems
# co-occur, document which error wins, determined empirically — invalid
# sortBy beats non-array/null input, and missing-input beats missing-sortBy
# beats non-array input.
PRECEDENCE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="invalid_sortby_beats_non_array_input",
        expression={"$sortArray": {"input": "hello", "sortBy": 0}},
        error_code=SORT_ARRAY_INVALID_SORT_SCALAR_ERROR,
        msg="Invalid sortBy (0) is reported over non-array input",
    ),
    ExpressionTestCase(
        id="invalid_sortby_beats_null_input",
        expression={"$sortArray": {"input": "$arr", "sortBy": 0}},
        doc={"arr": None},
        error_code=SORT_ARRAY_INVALID_SORT_SCALAR_ERROR,
        msg="Invalid sortBy (0) is reported instead of null propagation",
    ),
    ExpressionTestCase(
        id="missing_input_beats_missing_sortby",
        expression={"$sortArray": {}},
        error_code=SORT_ARRAY_MISSING_INPUT_ERROR,
        msg="Missing input is reported before missing sortBy",
    ),
    ExpressionTestCase(
        id="missing_sortby_beats_non_array_input",
        expression={"$sortArray": {"input": "hello"}},
        error_code=SORT_ARRAY_MISSING_SORTBY_ERROR,
        msg="Missing sortBy is reported before a non-array input type error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PRECEDENCE_ERROR_TESTS))
def test_sortArray_error_precedence(collection, test):
    """Document which error wins when multiple argument problems co-occur (Rule 18)."""
    if test.doc is not None:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    else:
        result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
