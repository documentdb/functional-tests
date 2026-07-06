"""
Error tests for $indexOfArray expression.

Tests non-array first argument, non-integral start/end, negative start/end,
boundary values, negative zero, and wrong arity errors.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.indexOfArray.utils.indexOfArray_common import (  # noqa: E501
    IndexOfArrayTest,
    build_args,
    build_insert_args,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_ARITY_ERROR,
    INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
    INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
    INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    INT32_MAX,
    INT64_MAX,
    MISSING,
)

# ---------------------------------------------------------------------------
# Success: boundary values for start/end indices
# ---------------------------------------------------------------------------
BOUNDARY_INDEX_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="start_int32_max",
        array=[1, 2, 3],
        search=1,
        start=INT32_MAX,
        expected=-1,
        msg="Should return -1 with INT32_MAX start",
    ),
    IndexOfArrayTest(
        id="start_int64_max",
        array=[1, 2, 3],
        search=1,
        start=INT64_MAX,
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject INT64_MAX start",
    ),
    IndexOfArrayTest(
        id="end_int32_max",
        array=[1, 2, 3],
        search=2,
        start=0,
        end=INT32_MAX,
        expected=1,
        msg="Should find with INT32_MAX end",
    ),
    IndexOfArrayTest(
        id="end_int64_max",
        array=[1, 2, 3],
        search=2,
        start=0,
        end=INT64_MAX,
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject INT64_MAX end",
    ),
    IndexOfArrayTest(
        id="start_and_end_int32_max",
        array=[1, 2, 3],
        search=1,
        start=INT32_MAX,
        end=INT32_MAX,
        expected=-1,
        msg="Should return -1 with both INT32_MAX",
    ),
    IndexOfArrayTest(
        id="start_int32_max_minus_1",
        array=[1, 2, 3],
        search=1,
        start=INT32_MAX - 1,
        expected=-1,
        msg="Should return -1 with INT32_MAX-1 start",
    ),
]

# ---------------------------------------------------------------------------
# Success: negative zero as start index
# ---------------------------------------------------------------------------
NEGATIVE_ZERO_START_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="double_neg_zero_start",
        array=[10, 20, 30],
        search=10,
        start=-0.0,
        expected=0,
        msg="Should treat -0.0 start as 0",
    ),
    IndexOfArrayTest(
        id="decimal128_neg_zero_start",
        array=[10, 20, 30],
        search=10,
        start=DECIMAL128_NEGATIVE_ZERO,
        expected=0,
        msg="Should treat decimal128 -0 start as 0",
    ),
    IndexOfArrayTest(
        id="double_neg_zero_end",
        array=[10, 20, 30],
        search=10,
        start=0,
        end=-0.0,
        expected=-1,
        msg="Should treat -0.0 end as 0",
    ),
]

# ---------------------------------------------------------------------------
# Error: first argument not an array (and not null)
# ---------------------------------------------------------------------------
NOT_ARRAY_ERROR_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="string_as_array",
        array="hello",
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject string as array",
    ),
    IndexOfArrayTest(
        id="int_as_array",
        array=42,
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject int as array",
    ),
    IndexOfArrayTest(
        id="double_as_array",
        array=3.14,
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject double as array",
    ),
    IndexOfArrayTest(
        id="bool_true_as_array",
        array=True,
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject bool true as array",
    ),
    IndexOfArrayTest(
        id="bool_false_as_array",
        array=False,
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject bool false as array",
    ),
    IndexOfArrayTest(
        id="object_as_array",
        array={"a": 1},
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject object as array",
    ),
    IndexOfArrayTest(
        id="decimal128_as_array",
        array=Decimal128("1"),
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject decimal128 as array",
    ),
    IndexOfArrayTest(
        id="int64_as_array",
        array=Int64(1),
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject int64 as array",
    ),
    IndexOfArrayTest(
        id="binary_as_array",
        array=Binary(b"x", 0),
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject binary as array",
    ),
    IndexOfArrayTest(
        id="datetime_as_array",
        array=datetime(2024, 1, 1),
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject datetime as array",
    ),
    IndexOfArrayTest(
        id="objectid_as_array",
        array=ObjectId(),
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject objectid as array",
    ),
    IndexOfArrayTest(
        id="regex_as_array",
        array=Regex("x"),
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject regex as array",
    ),
    IndexOfArrayTest(
        id="maxkey_as_array",
        array=MaxKey(),
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject maxkey as array",
    ),
    IndexOfArrayTest(
        id="minkey_as_array",
        array=MinKey(),
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject minkey as array",
    ),
    IndexOfArrayTest(
        id="timestamp_as_array",
        array=Timestamp(0, 0),
        search=1,
        error_code=INDEX_OF_ARRAY_NOT_ARRAY_ERROR,
        msg="Should reject timestamp as array",
    ),
]

# ---------------------------------------------------------------------------
# Error: start index not integral
# ---------------------------------------------------------------------------
START_NOT_INTEGRAL_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="start_fractional_double",
        array=[1, 2, 3],
        search=1,
        start=1.5,
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject fractional double start",
    ),
    IndexOfArrayTest(
        id="start_fractional_decimal128",
        array=[1, 2, 3],
        search=1,
        start=Decimal128("0.5"),
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject fractional decimal128 start",
    ),
    IndexOfArrayTest(
        id="start_nan",
        array=[1, 2, 3],
        search=1,
        start=float("nan"),
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject NaN start",
    ),
    IndexOfArrayTest(
        id="start_inf",
        array=[1, 2, 3],
        search=1,
        start=float("inf"),
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject infinity start",
    ),
    IndexOfArrayTest(
        id="start_neg_inf",
        array=[1, 2, 3],
        search=1,
        start=float("-inf"),
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject -infinity start",
    ),
    IndexOfArrayTest(
        id="start_decimal128_nan",
        array=[1, 2, 3],
        search=1,
        start=Decimal128("NaN"),
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject decimal128 NaN start",
    ),
    IndexOfArrayTest(
        id="start_decimal128_inf",
        array=[1, 2, 3],
        search=1,
        start=Decimal128("Infinity"),
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject decimal128 infinity start",
    ),
    IndexOfArrayTest(
        id="start_string",
        array=[1, 2, 3],
        search=1,
        start="0",
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject string start",
    ),
    IndexOfArrayTest(
        id="start_bool",
        array=[1, 2, 3],
        search=1,
        start=True,
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject bool start",
    ),
    IndexOfArrayTest(
        id="start_array",
        array=[1, 2, 3],
        search=1,
        start=[0],
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject array start",
    ),
    IndexOfArrayTest(
        id="start_object",
        array=[1, 2, 3],
        search=1,
        start={"a": 0},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject object start",
    ),
]

# ---------------------------------------------------------------------------
# Error: end index not integral
# ---------------------------------------------------------------------------
END_NOT_INTEGRAL_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="end_fractional_double",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=1.5,
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject fractional double end",
    ),
    IndexOfArrayTest(
        id="end_fractional_decimal128",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=Decimal128("0.5"),
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject fractional decimal128 end",
    ),
    IndexOfArrayTest(
        id="end_nan",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=float("nan"),
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject NaN end",
    ),
    IndexOfArrayTest(
        id="end_inf",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=float("inf"),
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject infinity end",
    ),
    IndexOfArrayTest(
        id="end_string",
        array=[1, 2, 3],
        search=1,
        start=0,
        end="3",
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject string end",
    ),
    IndexOfArrayTest(
        id="end_bool",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=True,
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject bool end",
    ),
    IndexOfArrayTest(
        id="end_neg_inf",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=float("-inf"),
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject -infinity end",
    ),
    IndexOfArrayTest(
        id="end_decimal128_nan",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=Decimal128("NaN"),
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject decimal128 NaN end",
    ),
    IndexOfArrayTest(
        id="end_decimal128_inf",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=Decimal128("Infinity"),
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject decimal128 infinity end",
    ),
    IndexOfArrayTest(
        id="end_array",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=[3],
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject array end",
    ),
    IndexOfArrayTest(
        id="end_object",
        array=[1, 2, 3],
        search=1,
        start=0,
        end={"a": 0},
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject object end",
    ),
]

# ---------------------------------------------------------------------------
# Error: negative start index
# ---------------------------------------------------------------------------
START_NEGATIVE_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="start_neg_one",
        array=[1, 2, 3],
        search=1,
        start=-1,
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="Should reject negative start -1",
    ),
    IndexOfArrayTest(
        id="start_neg_large",
        array=[1, 2, 3],
        search=1,
        start=-100,
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="Should reject negative start -100",
    ),
    IndexOfArrayTest(
        id="start_neg_int64",
        array=[1, 2, 3],
        search=1,
        start=Int64(-1),
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="Should reject negative Int64 start",
    ),
    IndexOfArrayTest(
        id="start_neg_double",
        array=[1, 2, 3],
        search=1,
        start=-1.0,
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="Should reject negative double start",
    ),
    IndexOfArrayTest(
        id="start_neg_decimal128",
        array=[1, 2, 3],
        search=1,
        start=Decimal128("-1"),
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="Should reject negative decimal128 start",
    ),
]

# ---------------------------------------------------------------------------
# Error: negative end index
# ---------------------------------------------------------------------------
END_NEGATIVE_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="end_neg_one",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=-1,
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="Should reject negative end -1",
    ),
    IndexOfArrayTest(
        id="end_neg_large",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=-100,
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="Should reject negative end -100",
    ),
    IndexOfArrayTest(
        id="end_neg_int64",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=Int64(-1),
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="Should reject negative Int64 end",
    ),
    IndexOfArrayTest(
        id="end_neg_double",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=-1.0,
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="Should reject negative double end",
    ),
    IndexOfArrayTest(
        id="end_neg_decimal128",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=Decimal128("-1"),
        error_code=INDEX_OF_ARRAY_INDEX_NEGATIVE_ERROR,
        msg="Should reject negative decimal128 end",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_TESTS = (
    BOUNDARY_INDEX_TESTS
    + NEGATIVE_ZERO_START_TESTS
    + NOT_ARRAY_ERROR_TESTS
    + START_NOT_INTEGRAL_TESTS
    + END_NOT_INTEGRAL_TESTS
    + START_NEGATIVE_TESTS
    + END_NEGATIVE_TESTS
)

LITERAL_ONLY_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="start_missing_field",
        array=[1, 2, 3],
        search=1,
        start=MISSING,
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject missing field as start",
    ),
    IndexOfArrayTest(
        id="end_missing_field",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=MISSING,
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Should reject missing field as end",
    ),
]

TEST_SUBSET_FOR_LITERAL = [
    NOT_ARRAY_ERROR_TESTS[0],  # string_as_array
    START_NOT_INTEGRAL_TESTS[0],  # start_fractional_double
    START_NEGATIVE_TESTS[0],  # start_neg_one
] + LITERAL_ONLY_TESTS


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_indexOfArray_literal(collection, test):
    """Test $indexOfArray error cases with literal values."""
    result = execute_expression(collection, {"$indexOfArray": build_args(test)})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_indexOfArray_insert(collection, test):
    """Test $indexOfArray error cases with values from inserted documents."""
    args, doc = build_insert_args(test)
    result = execute_expression_with_insert(collection, {"$indexOfArray": args}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# ---------------------------------------------------------------------------
# Error: wrong arity
# ---------------------------------------------------------------------------
ARITY_ERROR_TESTS = [
    pytest.param({"$indexOfArray": []}, id="zero_args"),
    pytest.param({"$indexOfArray": [[1, 2, 3]]}, id="one_arg"),
    pytest.param({"$indexOfArray": [[1, 2, 3], 1, 0, 3, 99]}, id="five_args"),
]


@pytest.mark.parametrize("expr", ARITY_ERROR_TESTS)
def test_indexOfArray_arity_error(collection, expr):
    """Test $indexOfArray errors with wrong number of arguments."""
    result = execute_expression(collection, expr)
    assert_expression_result(result, error_code=EXPRESSION_ARITY_ERROR)


# ---------------------------------------------------------------------------
# Error: null as literal start/end index
# Standalone test because end=None in IndexOfArrayTest means "no end argument",
# so null-as-end cannot be expressed via the dataclass.
# ---------------------------------------------------------------------------
def test_indexOfArray_null_end(collection):
    """Test $indexOfArray with null as end index errors."""
    result = execute_expression(collection, {"$indexOfArray": [[1, 2, 3], 1, 0, None]})
    assert_expression_result(
        result, error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR, msg="Null end should fail"
    )


def test_indexOfArray_null_start(collection):
    """Test $indexOfArray with null as start index errors."""

    result = execute_expression(collection, {"$indexOfArray": [[1, 2, 3], 1, None]})

    assert_expression_result(
        result,
        error_code=INDEX_OF_ARRAY_INDEX_NOT_INTEGRAL_ERROR,
        msg="Null start should fail",
    )
