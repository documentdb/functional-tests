"""
Error tests for $range expression.

Tests non-numeric types, non-integral values, step zero, out-of-range
int32 values, and wrong arity.

"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.range.utils.range_common import (  # noqa: E501
    RangeTest,
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
NON_NUMERIC_START_TESTS: list[RangeTest] = [
    RangeTest(
        id="string_start",
        start="hello",
        end=5,
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject string start",
    ),
    RangeTest(
        id="bool_start",
        start=True,
        end=5,
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject bool start",
    ),
    RangeTest(
        id="null_start",
        start=None,
        end=5,
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject null start",
    ),
    RangeTest(
        id="object_start",
        start={"a": 1},
        end=5,
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject object start",
    ),
    RangeTest(
        id="array_start",
        start=[1],
        end=5,
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject array start",
    ),
    RangeTest(
        id="objectid_start",
        start=ObjectId(),
        end=5,
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject objectid start",
    ),
    RangeTest(
        id="datetime_start",
        start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end=5,
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject datetime start",
    ),
    RangeTest(
        id="binary_start",
        start=Binary(b"x", 0),
        end=5,
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject binary start",
    ),
    RangeTest(
        id="regex_start",
        start=Regex("x"),
        end=5,
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject regex start",
    ),
    RangeTest(
        id="maxkey_start",
        start=MaxKey(),
        end=5,
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject maxkey start",
    ),
    RangeTest(
        id="minkey_start",
        start=MinKey(),
        end=5,
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject minkey start",
    ),
    RangeTest(
        id="timestamp_start",
        start=Timestamp(0, 0),
        end=5,
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject timestamp start",
    ),
]

# Error: non-numeric end
NON_NUMERIC_END_TESTS: list[RangeTest] = [
    RangeTest(
        id="string_end",
        start=0,
        end="hello",
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject string end",
    ),
    RangeTest(
        id="bool_end",
        start=0,
        end=True,
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject bool end",
    ),
    RangeTest(
        id="null_end",
        start=0,
        end=None,
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject null end",
    ),
    RangeTest(
        id="object_end",
        start=0,
        end={"a": 1},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject object end",
    ),
    RangeTest(
        id="array_end",
        start=0,
        end=[1],
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject array end",
    ),
    RangeTest(
        id="objectid_end",
        start=0,
        end=ObjectId(),
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject objectid end",
    ),
    RangeTest(
        id="datetime_end",
        start=0,
        end=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject datetime end",
    ),
    RangeTest(
        id="binary_end",
        start=0,
        end=Binary(b"x", 0),
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject binary end",
    ),
    RangeTest(
        id="regex_end",
        start=0,
        end=Regex("x"),
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject regex end",
    ),
    RangeTest(
        id="maxkey_end",
        start=0,
        end=MaxKey(),
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject maxkey end",
    ),
    RangeTest(
        id="minkey_end",
        start=0,
        end=MinKey(),
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject minkey end",
    ),
    RangeTest(
        id="timestamp_end",
        start=0,
        end=Timestamp(0, 0),
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject timestamp end",
    ),
]

# Error: non-numeric step
NON_NUMERIC_STEP_TESTS: list[RangeTest] = [
    RangeTest(
        id="string_step",
        start=0,
        end=5,
        step="bad",
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject string step",
    ),
    RangeTest(
        id="bool_step",
        start=0,
        end=5,
        step=True,
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject bool step",
    ),
    RangeTest(
        id="object_step",
        start=0,
        end=5,
        step={"a": 1},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject object step",
    ),
    RangeTest(
        id="array_step",
        start=0,
        end=5,
        step=[1],
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject array step",
    ),
    RangeTest(
        id="objectid_step",
        start=0,
        end=5,
        step=ObjectId(),
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject objectid step",
    ),
    RangeTest(
        id="datetime_step",
        start=0,
        end=5,
        step=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject datetime step",
    ),
    RangeTest(
        id="binary_step",
        start=0,
        end=5,
        step=Binary(b"x", 0),
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject binary step",
    ),
    RangeTest(
        id="regex_step",
        start=0,
        end=5,
        step=Regex("x"),
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject regex step",
    ),
    RangeTest(
        id="maxkey_step",
        start=0,
        end=5,
        step=MaxKey(),
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject maxkey step",
    ),
    RangeTest(
        id="minkey_step",
        start=0,
        end=5,
        step=MinKey(),
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject minkey step",
    ),
    RangeTest(
        id="timestamp_step",
        start=0,
        end=5,
        step=Timestamp(0, 0),
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject timestamp step",
    ),
]

# Error: non-integral start
NON_INTEGRAL_START_TESTS: list[RangeTest] = [
    RangeTest(
        id="fractional_start",
        start=1.5,
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject fractional start",
    ),
    RangeTest(
        id="decimal128_fractional_start",
        start=Decimal128("0.5"),
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject fractional Decimal128 start",
    ),
    RangeTest(
        id="negative_fractional_start",
        start=-1.5,
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject negative fractional start",
    ),
    RangeTest(
        id="decimal128_negative_fractional_start",
        start=Decimal128("-1.5"),
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject negative fractional Decimal128 start",
    ),
    RangeTest(
        id="decimal128_negative_nan_start",
        start=Decimal128("-NaN"),
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject Decimal128 -NaN start",
    ),
]

# Error: non-integral end
NON_INTEGRAL_END_TESTS: list[RangeTest] = [
    RangeTest(
        id="fractional_end",
        start=0,
        end=5.5,
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject fractional end",
    ),
    RangeTest(
        id="decimal128_fractional_end",
        start=0,
        end=Decimal128("5.5"),
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject fractional Decimal128 end",
    ),
    RangeTest(
        id="negative_fractional_end",
        start=0,
        end=-1.5,
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject negative fractional end",
    ),
    RangeTest(
        id="decimal128_negative_fractional_end",
        start=0,
        end=Decimal128("-1.5"),
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject negative fractional Decimal128 end",
    ),
]

# Error: non-integral step
NON_INTEGRAL_STEP_TESTS: list[RangeTest] = [
    RangeTest(
        id="fractional_step",
        start=0,
        end=10,
        step=1.5,
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject fractional step",
    ),
    RangeTest(
        id="decimal128_fractional_step",
        start=0,
        end=10,
        step=Decimal128("1.5"),
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject fractional Decimal128 step",
    ),
    RangeTest(
        id="negative_fractional_step",
        start=10,
        end=0,
        step=-1.5,
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject negative fractional step",
    ),
    RangeTest(
        id="decimal128_negative_fractional_step",
        start=10,
        end=0,
        step=Decimal128("-1.5"),
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject negative fractional Decimal128 step",
    ),
]

# Error: special numeric values
# Property [Special Numerics]: $map preserves NaN, Infinity, and boundary values.
SPECIAL_NUMERIC_TESTS: list[RangeTest] = [
    RangeTest(
        id="nan_start",
        start=FLOAT_NAN,
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject NaN start",
    ),
    RangeTest(
        id="inf_start",
        start=FLOAT_INFINITY,
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject Infinity start",
    ),
    RangeTest(
        id="neg_inf_start",
        start=FLOAT_NEGATIVE_INFINITY,
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject -Infinity start",
    ),
    RangeTest(
        id="nan_end",
        start=0,
        end=FLOAT_NAN,
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject NaN end",
    ),
    RangeTest(
        id="inf_end",
        start=0,
        end=FLOAT_INFINITY,
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject Infinity end",
    ),
    RangeTest(
        id="decimal128_nan_start",
        start=DECIMAL128_NAN,
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject Decimal128 NaN start",
    ),
    RangeTest(
        id="decimal128_inf_start",
        start=DECIMAL128_INFINITY,
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject Decimal128 Infinity start",
    ),
    RangeTest(
        id="decimal128_neg_inf_end",
        start=0,
        end=DECIMAL128_NEGATIVE_INFINITY,
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject Decimal128 -Infinity end",
    ),
]

# Error: step zero → 34449
# Property [Step Zero]: $range rejects zero step value.
STEP_ZERO_TESTS: list[RangeTest] = [
    RangeTest(
        id="step_zero_int",
        start=0,
        end=5,
        step=0,
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="Should reject step 0",
    ),
    RangeTest(
        id="step_zero_int64",
        start=0,
        end=5,
        step=Int64(0),
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="Should reject Int64 step 0",
    ),
    RangeTest(
        id="step_zero_double",
        start=0,
        end=5,
        step=0.0,
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="Should reject double step 0.0",
    ),
    RangeTest(
        id="step_zero_decimal128",
        start=0,
        end=5,
        step=Decimal128("0"),
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="Should reject Decimal128 step 0",
    ),
    RangeTest(
        id="step_neg_zero_double",
        start=0,
        end=5,
        step=-0.0,
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="Should reject negative zero double step",
    ),
    RangeTest(
        id="step_neg_zero_decimal128",
        start=0,
        end=5,
        step=Decimal128("-0"),
        error_code=RANGE_STEP_ZERO_ERROR,
        msg="Should reject negative zero Decimal128 step",
    ),
]

# Error: out of int32 range
OUT_OF_INT32_TESTS: list[RangeTest] = [
    RangeTest(
        id="start_int64_max",
        start=INT64_MAX,
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject INT64_MAX start",
    ),
    RangeTest(
        id="start_int64_min",
        start=INT64_MIN,
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject INT64_MIN start",
    ),
    RangeTest(
        id="end_int64_max",
        start=0,
        end=INT64_MAX,
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject INT64_MAX end",
    ),
    RangeTest(
        id="end_int64_min",
        start=0,
        end=INT64_MIN,
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject INT64_MIN end",
    ),
    RangeTest(
        id="step_int64_max",
        start=0,
        end=5,
        step=INT64_MAX,
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject INT64_MAX step",
    ),
    RangeTest(
        id="start_int32_overflow",
        start=INT32_OVERFLOW,
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject INT32_OVERFLOW start",
    ),
    RangeTest(
        id="start_int32_underflow",
        start=INT32_UNDERFLOW,
        end=5,
        error_code=RANGE_START_NOT_INTEGRAL_ERROR,
        msg="Should reject INT32_UNDERFLOW start",
    ),
    RangeTest(
        id="end_int32_overflow",
        start=0,
        end=INT32_OVERFLOW,
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject INT32_OVERFLOW end",
    ),
    RangeTest(
        id="end_int32_underflow",
        start=0,
        end=INT32_UNDERFLOW,
        error_code=RANGE_END_NOT_INT32_ERROR,
        msg="Should reject INT32_UNDERFLOW end",
    ),
    RangeTest(
        id="step_int32_overflow",
        start=0,
        end=5,
        step=INT32_OVERFLOW,
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject INT32_OVERFLOW step",
    ),
    RangeTest(
        id="step_int32_underflow",
        start=0,
        end=5,
        step=INT32_UNDERFLOW,
        error_code=RANGE_STEP_NOT_INT32_ERROR,
        msg="Should reject INT32_UNDERFLOW step",
    ),
]

# Aggregate and test
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
)


TEST_SUBSET_FOR_LITERAL = [
    NON_NUMERIC_START_TESTS[0],  # string_start
    NON_INTEGRAL_START_TESTS[0],  # fractional_start
    SPECIAL_NUMERIC_TESTS[0],  # nan_start
    STEP_ZERO_TESTS[0],  # step_zero_int
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_range_error_literal(collection, test):
    """Test $range error with literal values."""
    args = [test.start, test.end]
    if test.step is not None:
        args.append(test.step)
    result = execute_expression(collection, {"$range": args})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_range_error_insert(collection, test):
    """Test $range error with values from inserted documents."""
    doc = {"start": test.start, "end": test.end}
    args = ["$start", "$end"]
    if test.step is not None:
        args.append("$step")
        doc["step"] = test.step
    result = execute_expression_with_insert(collection, {"$range": args}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Error: wrong arity
ARITY_ERROR_TESTS = [
    pytest.param({"$range": []}, id="zero_args"),
    pytest.param({"$range": [1]}, id="one_arg"),
    pytest.param({"$range": [1, 2, 3, 4]}, id="four_args"),
]


@pytest.mark.parametrize("expr", ARITY_ERROR_TESTS)
def test_range_arity_error(collection, expr):
    """Test $range errors with wrong number of arguments."""
    result = execute_expression(collection, expr)
    assert_expression_result(result, error_code=EXPRESSION_ARITY_ERROR)
