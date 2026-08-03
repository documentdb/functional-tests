"""
Error tests for $reverseArray expression.

Tests non-array input (all BSON types, special numeric values, boundary values,
string edge cases), wrong arity, and literal-wrapped non-array resolution.
Note: unlike $size, $reverseArray propagates null — null/missing field-path
tests are in test_expression_reverseArray_expressions.py.
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
    EXPRESSION_TYPE_MISMATCH_ERROR,
    REVERSE_ARRAY_NOT_ARRAY_ERROR,
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

# Property [Literal-path parity]: representative non-array rejections also run
# through the literal-value path (not just via inserted documents). Defined
# here directly (not by positional index into the groups below) so the
# mapping is name-stable, and appended to ALL_TESTS below so they also get
# insert coverage.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_input",
        expression={"$reverseArray": "hello"},
        doc={"arr": "hello"},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject string input",
    ),
    ExpressionTestCase(
        id="timestamp_input",
        expression={"$reverseArray": Timestamp(0, 0)},
        doc={"arr": Timestamp(0, 0)},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject timestamp input",
    ),
    ExpressionTestCase(
        id="nan_input",
        expression={"$reverseArray": FLOAT_NAN},
        doc={"arr": FLOAT_NAN},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject NaN input",
    ),
    ExpressionTestCase(
        id="int32_max_input",
        expression={"$reverseArray": INT32_MAX},
        doc={"arr": INT32_MAX},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject INT32_MAX input",
    ),
]

# Property [Arity errors]: $reverseArray requires exactly one argument; zero,
# two, or three arguments are rejected with EXPRESSION_TYPE_MISMATCH_ERROR.
# These have no doc, so they only run through the literal path below.
ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="zero_args",
        expression={"$reverseArray": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="A literal empty argument array is treated as zero arguments",
    ),
    ExpressionTestCase(
        id="two_args",
        expression={"$reverseArray": [[], []]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject two arguments",
    ),
    ExpressionTestCase(
        id="three_args",
        expression={"$reverseArray": ["$a", "$b", "$c"]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject three arguments",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL + ARITY_ERROR_TESTS))
def test_reverseArray_not_array_literal(collection, test):
    """Test $reverseArray error with non-array literal input."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Non-array rejection]: every non-array BSON type (scalar, object,
# and edge values like empty object/negative numbers) is rejected with
# REVERSE_ARRAY_NOT_ARRAY_ERROR — no type is silently coerced or unwrapped.
NOT_ARRAY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": 42},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject int input",
    ),
    ExpressionTestCase(
        id="negative_int_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": -42},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject negative int input",
    ),
    ExpressionTestCase(
        id="bool_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": True},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject bool input",
    ),
    ExpressionTestCase(
        id="object_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": {"a": 1}},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject object input",
    ),
    ExpressionTestCase(
        id="empty_object_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": {}},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject empty object input (contrast with [] which succeeds)",
    ),
    ExpressionTestCase(
        id="double_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": 3.14},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject double input",
    ),
    ExpressionTestCase(
        id="negative_double_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": -3.14},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject negative double input",
    ),
    ExpressionTestCase(
        id="decimal128_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": Decimal128("1")},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject decimal128 input",
    ),
    ExpressionTestCase(
        id="int64_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": Int64(1)},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject int64 input",
    ),
    ExpressionTestCase(
        id="objectid_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": ObjectId()},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject objectid input",
    ),
    ExpressionTestCase(
        id="datetime_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject datetime input",
    ),
    ExpressionTestCase(
        id="binary_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": Binary(b"x", 0)},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject binary input",
    ),
    ExpressionTestCase(
        id="regex_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": Regex("x")},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject regex input",
    ),
    ExpressionTestCase(
        id="maxkey_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": MaxKey()},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject maxkey input",
    ),
    ExpressionTestCase(
        id="minkey_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": MinKey()},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject minkey input",
    ),
]

# Property [Special numeric non-array rejection]: IEEE-754/Decimal128 special
# numeric values (±Infinity, ±0, NaN) are still scalars, not arrays, and are
# rejected the same as any other non-array input.
SPECIAL_NUMERIC_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="inf_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": FLOAT_INFINITY},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject Infinity input",
    ),
    ExpressionTestCase(
        id="neg_inf_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": FLOAT_NEGATIVE_INFINITY},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject -Infinity input",
    ),
    ExpressionTestCase(
        id="neg_zero_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": DOUBLE_NEGATIVE_ZERO},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject negative zero input",
    ),
    ExpressionTestCase(
        id="decimal128_nan_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": DECIMAL128_NAN},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 NaN input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_nan_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": DECIMAL128_NEGATIVE_NAN},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -NaN input",
    ),
    ExpressionTestCase(
        id="decimal128_inf_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": DECIMAL128_INFINITY},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 Infinity input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_inf_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": DECIMAL128_NEGATIVE_INFINITY},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -Infinity input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_zero_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": DECIMAL128_NEGATIVE_ZERO},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject Decimal128 -0 input",
    ),
]

# Property [Boundary-value non-array rejection]: min/max values for each
# numeric BSON type (Int32, Int64, Decimal128) are rejected the same as any
# other non-array scalar — the not-array check has no numeric-magnitude
# special-casing at the boundaries.
BOUNDARY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int32_min_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": INT32_MIN},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject INT32_MIN input",
    ),
    ExpressionTestCase(
        id="int64_max_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": INT64_MAX},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject INT64_MAX input",
    ),
    ExpressionTestCase(
        id="int64_min_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": INT64_MIN},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject INT64_MIN input",
    ),
    ExpressionTestCase(
        id="decimal128_max_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": DECIMAL128_MAX},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject DECIMAL128_MAX input",
    ),
    ExpressionTestCase(
        id="decimal128_min_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": DECIMAL128_MIN},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject DECIMAL128_MIN input",
    ),
]

# Property [String-shape non-array rejection]: strings that merely look like
# array syntax (comma-separated or JSON array text) are still the string BSON
# type and are rejected, not parsed or reinterpreted as an array.
STRING_EDGE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="comma_separated_string_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": "1, 2, 3"},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject comma-separated string",
    ),
    ExpressionTestCase(
        id="json_like_string_input",
        expression={"$reverseArray": "$arr"},
        doc={"arr": "[1, 2, 3]"},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject JSON-like string",
    ),
]

# Property [Expression-resolved non-array rejection]: an operand built by
# wrapping a non-array field reference in an array literal (e.g. [$a] where
# a=1) still resolves to a non-array value once evaluated, and is rejected
# like any other non-array input.
EXPRESSION_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="field_ref_wrapped_non_array",
        expression={"$reverseArray": ["$a"]},
        doc={"a": 1},
        error_code=REVERSE_ARRAY_NOT_ARRAY_ERROR,
        msg="[$a] where a=1 resolves to int, not array",
    ),
]

ALL_TESTS = (
    NOT_ARRAY_ERROR_TESTS
    + SPECIAL_NUMERIC_ERROR_TESTS
    + BOUNDARY_ERROR_TESTS
    + STRING_EDGE_ERROR_TESTS
    + TEST_SUBSET_FOR_LITERAL
    + EXPRESSION_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_reverseArray_not_array_insert(collection, test):
    """Test $reverseArray error with non-array input from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
