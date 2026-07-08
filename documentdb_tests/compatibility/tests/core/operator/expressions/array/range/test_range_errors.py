"""
Error tests for $range expression.

Tests non-numeric types, non-integral values, step zero, out-of-range
int32 values, and wrong arity.

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
    EXPRESSION_ARITY_ERROR,
    RANGE_END_NOT_INT32_ERROR,
    RANGE_END_NOT_NUMERIC_ERROR,
    RANGE_START_NOT_INT32_ERROR,
    RANGE_START_NOT_INTEGRAL_ERROR,
    RANGE_STEP_NOT_INT32_ERROR,
    RANGE_STEP_NOT_NUMERIC_ERROR,
    RANGE_STEP_ZERO_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MIN,
)

# Error: non-numeric start
NON_NUMERIC_START_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_start",
        doc={"start": "hello", "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject string start",
    ),
    ExpressionTestCase(
        id="bool_start",
        doc={"start": True, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject bool start",
    ),
    ExpressionTestCase(
        id="null_start",
        doc={"start": None, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject null start",
    ),
    ExpressionTestCase(
        id="object_start",
        doc={"start": {"a": 1}, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject object start",
    ),
    ExpressionTestCase(
        id="array_start",
        doc={"start": [1], "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject array start",
    ),
    ExpressionTestCase(
        id="objectid_start",
        doc={"start": ObjectId(), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject objectid start",
    ),
    ExpressionTestCase(
        id="datetime_start",
        doc={"start": datetime(2024, 1, 1, tzinfo=timezone.utc), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject datetime start",
    ),
    ExpressionTestCase(
        id="binary_start",
        doc={"start": Binary(b"x", 0), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject binary start",
    ),
    ExpressionTestCase(
        id="regex_start",
        doc={"start": Regex("x"), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject regex start",
    ),
    ExpressionTestCase(
        id="maxkey_start",
        doc={"start": MaxKey(), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject maxkey start",
    ),
    ExpressionTestCase(
        id="minkey_start",
        doc={"start": MinKey(), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject minkey start",
    ),
    ExpressionTestCase(
        id="timestamp_start",
        doc={"start": Timestamp(0, 0), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject timestamp start",
    ),
]

# Error: non-numeric end
NON_NUMERIC_END_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_end",
        doc={"start": 0, "end": "hello"},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject string end",
    ),
    ExpressionTestCase(
        id="bool_end",
        doc={"start": 0, "end": True},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject bool end",
    ),
    ExpressionTestCase(
        id="null_end",
        doc={"start": 0, "end": None},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject null end",
    ),
    ExpressionTestCase(
        id="object_end",
        doc={"start": 0, "end": {"a": 1}},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject object end",
    ),
    ExpressionTestCase(
        id="array_end",
        doc={"start": 0, "end": [1]},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject array end",
    ),
    ExpressionTestCase(
        id="objectid_end",
        doc={"start": 0, "end": ObjectId()},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject objectid end",
    ),
    ExpressionTestCase(
        id="datetime_end",
        doc={"start": 0, "end": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject datetime end",
    ),
    ExpressionTestCase(
        id="binary_end",
        doc={"start": 0, "end": Binary(b"x", 0)},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject binary end",
    ),
    ExpressionTestCase(
        id="regex_end",
        doc={"start": 0, "end": Regex("x")},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject regex end",
    ),
    ExpressionTestCase(
        id="maxkey_end",
        doc={"start": 0, "end": MaxKey()},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject maxkey end",
    ),
    ExpressionTestCase(
        id="minkey_end",
        doc={"start": 0, "end": MinKey()},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject minkey end",
    ),
    ExpressionTestCase(
        id="timestamp_end",
        doc={"start": 0, "end": Timestamp(0, 0)},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject timestamp end",
    ),
]

# Error: non-numeric step
NON_NUMERIC_STEP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_step",
        doc={"start": 0, "end": 5, "step": "bad"},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject string step",
    ),
    ExpressionTestCase(
        id="bool_step",
        doc={"start": 0, "end": 5, "step": True},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject bool step",
    ),
    ExpressionTestCase(
        id="object_step",
        doc={"start": 0, "end": 5, "step": {"a": 1}},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject object step",
    ),
    ExpressionTestCase(
        id="array_step",
        doc={"start": 0, "end": 5, "step": [1]},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject array step",
    ),
    ExpressionTestCase(
        id="objectid_step",
        doc={"start": 0, "end": 5, "step": ObjectId()},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject objectid step",
    ),
    ExpressionTestCase(
        id="datetime_step",
        doc={"start": 0, "end": 5, "step": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject datetime step",
    ),
    ExpressionTestCase(
        id="binary_step",
        doc={"start": 0, "end": 5, "step": Binary(b"x", 0)},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject binary step",
    ),
    ExpressionTestCase(
        id="regex_step",
        doc={"start": 0, "end": 5, "step": Regex("x")},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject regex step",
    ),
    ExpressionTestCase(
        id="maxkey_step",
        doc={"start": 0, "end": 5, "step": MaxKey()},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject maxkey step",
    ),
    ExpressionTestCase(
        id="minkey_step",
        doc={"start": 0, "end": 5, "step": MinKey()},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject minkey step",
    ),
    ExpressionTestCase(
        id="timestamp_step",
        doc={"start": 0, "end": 5, "step": Timestamp(0, 0)},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject timestamp step",
    ),
]

# Error: non-integral start
NON_INTEGRAL_START_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="fractional_start",
        doc={"start": 1.5, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject fractional start",
    ),
    ExpressionTestCase(
        id="decimal128_fractional_start",
        doc={"start": Decimal128("0.5"), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject fractional Decimal128 start",
    ),
    ExpressionTestCase(
        id="negative_fractional_start",
        doc={"start": -1.5, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject negative fractional start",
    ),
    ExpressionTestCase(
        id="decimal128_negative_fractional_start",
        doc={"start": Decimal128("-1.5"), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject negative fractional Decimal128 start",
    ),
    ExpressionTestCase(
        id="decimal128_negative_nan_start",
        doc={"start": Decimal128("-NaN"), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject Decimal128 -NaN start",
    ),
]

# Error: non-integral end
NON_INTEGRAL_END_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="fractional_end",
        doc={"start": 0, "end": 5.5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject fractional end",
    ),
    ExpressionTestCase(
        id="decimal128_fractional_end",
        doc={"start": 0, "end": Decimal128("5.5")},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject fractional Decimal128 end",
    ),
    ExpressionTestCase(
        id="negative_fractional_end",
        doc={"start": 0, "end": -1.5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject negative fractional end",
    ),
    ExpressionTestCase(
        id="decimal128_negative_fractional_end",
        doc={"start": 0, "end": Decimal128("-1.5")},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject negative fractional Decimal128 end",
    ),
]

# Error: non-integral step
NON_INTEGRAL_STEP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="fractional_step",
        doc={"start": 0, "end": 10, "step": 1.5},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject fractional step",
    ),
    ExpressionTestCase(
        id="decimal128_fractional_step",
        doc={"start": 0, "end": 10, "step": Decimal128("1.5")},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject fractional Decimal128 step",
    ),
    ExpressionTestCase(
        id="negative_fractional_step",
        doc={"start": 10, "end": 0, "step": -1.5},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject negative fractional step",
    ),
    ExpressionTestCase(
        id="decimal128_negative_fractional_step",
        doc={"start": 10, "end": 0, "step": Decimal128("-1.5")},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject negative fractional Decimal128 step",
    ),
]

# Error: special numeric values
# Property [Special Numerics]: $map preserves NaN, Infinity, and boundary values.
SPECIAL_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nan_start",
        doc={"start": FLOAT_NAN, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject NaN start",
    ),
    ExpressionTestCase(
        id="inf_start",
        doc={"start": FLOAT_INFINITY, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject Infinity start",
    ),
    ExpressionTestCase(
        id="neg_inf_start",
        doc={"start": FLOAT_NEGATIVE_INFINITY, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject -Infinity start",
    ),
    ExpressionTestCase(
        id="nan_end",
        doc={"start": 0, "end": FLOAT_NAN},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject NaN end",
    ),
    ExpressionTestCase(
        id="inf_end",
        doc={"start": 0, "end": FLOAT_INFINITY},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject Infinity end",
    ),
    ExpressionTestCase(
        id="decimal128_nan_start",
        doc={"start": DECIMAL128_NAN, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject Decimal128 NaN start",
    ),
    ExpressionTestCase(
        id="decimal128_inf_start",
        doc={"start": DECIMAL128_INFINITY, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject Decimal128 Infinity start",
    ),
    ExpressionTestCase(
        id="decimal128_neg_inf_end",
        doc={"start": 0, "end": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject Decimal128 -Infinity end",
    ),
]

# Error: step zero → 34449
# Property [Step Zero]: $range rejects zero step value.
STEP_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="step_zero_int",
        doc={"start": 0, "end": 5, "step": 0},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="Should reject step 0",
    ),
    ExpressionTestCase(
        id="step_zero_int64",
        doc={"start": 0, "end": 5, "step": Int64(0)},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="Should reject Int64 step 0",
    ),
    ExpressionTestCase(
        id="step_zero_double",
        doc={"start": 0, "end": 5, "step": 0.0},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="Should reject double step 0.0",
    ),
    ExpressionTestCase(
        id="step_zero_decimal128",
        doc={"start": 0, "end": 5, "step": Decimal128("0")},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="Should reject Decimal128 step 0",
    ),
    ExpressionTestCase(
        id="step_neg_zero_double",
        doc={"start": 0, "end": 5, "step": -0.0},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="Should reject negative zero double step",
    ),
    ExpressionTestCase(
        id="step_neg_zero_decimal128",
        doc={"start": 0, "end": 5, "step": Decimal128("-0")},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="Should reject negative zero Decimal128 step",
    ),
]

# Error: out of int32 range
OUT_OF_INT32_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="start_int64_max",
        doc={"start": INT64_MAX, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject INT64_MAX start",
    ),
    ExpressionTestCase(
        id="start_int64_min",
        doc={"start": INT64_MIN, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject INT64_MIN start",
    ),
    ExpressionTestCase(
        id="end_int64_max",
        doc={"start": 0, "end": INT64_MAX},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject INT64_MAX end",
    ),
    ExpressionTestCase(
        id="end_int64_min",
        doc={"start": 0, "end": INT64_MIN},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject INT64_MIN end",
    ),
    ExpressionTestCase(
        id="step_int64_max",
        doc={"start": 0, "end": 5, "step": INT64_MAX},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject INT64_MAX step",
    ),
    ExpressionTestCase(
        id="start_int32_overflow",
        doc={"start": INT32_OVERFLOW, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject INT32_OVERFLOW start",
    ),
    ExpressionTestCase(
        id="start_int32_underflow",
        doc={"start": INT32_UNDERFLOW, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject INT32_UNDERFLOW start",
    ),
    ExpressionTestCase(
        id="end_int32_overflow",
        doc={"start": 0, "end": INT32_OVERFLOW},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject INT32_OVERFLOW end",
    ),
    ExpressionTestCase(
        id="end_int32_underflow",
        doc={"start": 0, "end": INT32_UNDERFLOW},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject INT32_UNDERFLOW end",
    ),
    ExpressionTestCase(
        id="step_int32_overflow",
        doc={"start": 0, "end": 5, "step": INT32_OVERFLOW},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject INT32_OVERFLOW step",
    ),
    ExpressionTestCase(
        id="step_int32_underflow",
        doc={"start": 0, "end": 5, "step": INT32_UNDERFLOW},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject INT32_UNDERFLOW step",
    ),
]

# Aggregate and test
# Error: wrong arity
ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="zero_args",
        expression={"$range": []},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="Should error with zero arguments",
    ),
    ExpressionTestCase(
        id="one_arg",
        expression={"$range": [1]},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="Should error with one argument",
    ),
    ExpressionTestCase(
        id="four_args",
        expression={"$range": [1, 2, 3, 4]},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="Should error with four arguments",
    ),
]

ALL_TESTS = (
    NON_NUMERIC_START_TESTS
    + NON_NUMERIC_END_TESTS
    + NON_NUMERIC_STEP_TESTS
    + NON_INTEGRAL_START_TESTS
    + NON_INTEGRAL_END_TESTS
    + NON_INTEGRAL_STEP_TESTS
    + SPECIAL_NUMERIC_TESTS
    + STEP_ZERO_TESTS
    + OUT_OF_INT32_TESTS
    + ARITY_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_range_error_insert(collection, test):
    """Test $range error with values from inserted documents."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
