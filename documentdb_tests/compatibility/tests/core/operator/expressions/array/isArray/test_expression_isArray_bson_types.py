"""
BSON type tests for $isArray expression.

Tests arrays containing specific BSON types return true,
non-array BSON types return false, special numeric values,
and boundary values.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.isArray.utils.isArray_common import (  # noqa: E501
    IsArrayTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
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
# Arrays containing specific BSON types → true
# ---------------------------------------------------------------------------
BSON_ARRAY_TRUE_TESTS: list[IsArrayTest] = [
    IsArrayTest(
        id="bindata_array",
        value=[Binary(b"\x00", 0)],
        expected=True,
        msg="Should return true for BinData array",
    ),
    IsArrayTest(
        id="timestamp_array",
        value=[Timestamp(0, 0)],
        expected=True,
        msg="Should return true for Timestamp array",
    ),
    IsArrayTest(
        id="int64_array", value=[Int64(1)], expected=True, msg="Should return true for Int64 array"
    ),
    IsArrayTest(
        id="decimal128_array",
        value=[Decimal128("1")],
        expected=True,
        msg="Should return true for Decimal128 array",
    ),
    IsArrayTest(
        id="objectid_array",
        value=[ObjectId()],
        expected=True,
        msg="Should return true for ObjectId array",
    ),
    IsArrayTest(
        id="datetime_array",
        value=[datetime(2024, 1, 1)],
        expected=True,
        msg="Should return true for datetime array",
    ),
    IsArrayTest(
        id="minkey_array",
        value=[MinKey()],
        expected=True,
        msg="Should return true for MinKey array",
    ),
    IsArrayTest(
        id="maxkey_array",
        value=[MaxKey()],
        expected=True,
        msg="Should return true for MaxKey array",
    ),
    IsArrayTest(
        id="regex_array",
        value=[Regex(".*")],
        expected=True,
        msg="Should return true for Regex array",
    ),
    IsArrayTest(
        id="nan_array", value=[float("nan")], expected=True, msg="Should return true for NaN array"
    ),
    IsArrayTest(
        id="inf_array",
        value=[float("inf")],
        expected=True,
        msg="Should return true for Infinity array",
    ),
    IsArrayTest(
        id="decimal128_nan_array",
        value=[Decimal128("NaN")],
        expected=True,
        msg="Should return true for Decimal128 NaN array",
    ),
    IsArrayTest(
        id="decimal128_inf_array",
        value=[Decimal128("Infinity")],
        expected=True,
        msg="Should return true for Decimal128 Infinity array",
    ),
    IsArrayTest(
        id="decimal128_neg_nan_array",
        value=[Decimal128("-NaN")],
        expected=True,
        msg="Should return true for Decimal128 -NaN array",
    ),
    IsArrayTest(
        id="decimal128_neg_inf_array",
        value=[DECIMAL128_NEGATIVE_INFINITY],
        expected=True,
        msg="Should return true for Decimal128 -Infinity array",
    ),
    IsArrayTest(
        id="neg_inf_array",
        value=[FLOAT_NEGATIVE_INFINITY],
        expected=True,
        msg="Should return true for -Infinity array",
    ),
    IsArrayTest(
        id="neg_zero_array",
        value=[DOUBLE_NEGATIVE_ZERO],
        expected=True,
        msg="Should return true for negative zero array",
    ),
    IsArrayTest(
        id="decimal128_neg_zero_array",
        value=[DECIMAL128_NEGATIVE_ZERO],
        expected=True,
        msg="Should return true for Decimal128 -0 array",
    ),
    IsArrayTest(
        id="nested_mixed_bson_array",
        value=[
            MinKey(),
            {"a": [Decimal128("1.5")]},
            Int64(1),
            datetime(2024, 1, 1),
            Binary(b"\x01", 0),
        ],
        expected=True,
        msg="Should return true for nested mixed BSON array",
    ),
]

# ---------------------------------------------------------------------------
# Non-array BSON types → false
# ---------------------------------------------------------------------------
BSON_FALSE_TESTS: list[IsArrayTest] = [
    IsArrayTest(id="int64", value=Int64(1), expected=False, msg="Should return false for Int64"),
    IsArrayTest(
        id="decimal128",
        value=Decimal128("1"),
        expected=False,
        msg="Should return false for Decimal128",
    ),
    IsArrayTest(
        id="objectid",
        value=ObjectId("000000000000000000000001"),
        expected=False,
        msg="Should return false for ObjectId",
    ),
    IsArrayTest(
        id="datetime",
        value=datetime(2024, 1, 1),
        expected=False,
        msg="Should return false for datetime",
    ),
    IsArrayTest(
        id="binary", value=Binary(b"\x01", 0), expected=False, msg="Should return false for Binary"
    ),
    IsArrayTest(
        id="regex", value=Regex("^abc"), expected=False, msg="Should return false for Regex"
    ),
    IsArrayTest(
        id="timestamp",
        value=Timestamp(1, 1),
        expected=False,
        msg="Should return false for Timestamp",
    ),
    IsArrayTest(id="minkey", value=MinKey(), expected=False, msg="Should return false for MinKey"),
    IsArrayTest(id="maxkey", value=MaxKey(), expected=False, msg="Should return false for MaxKey"),
]

# ---------------------------------------------------------------------------
# Special numeric values → false
# ---------------------------------------------------------------------------
SPECIAL_NUMERIC_TESTS: list[IsArrayTest] = [
    IsArrayTest(id="nan", value=FLOAT_NAN, expected=False, msg="Should return false for NaN"),
    IsArrayTest(
        id="inf", value=FLOAT_INFINITY, expected=False, msg="Should return false for Infinity"
    ),
    IsArrayTest(
        id="neg_inf",
        value=FLOAT_NEGATIVE_INFINITY,
        expected=False,
        msg="Should return false for -Infinity",
    ),
    IsArrayTest(
        id="neg_zero",
        value=DOUBLE_NEGATIVE_ZERO,
        expected=False,
        msg="Should return false for negative zero",
    ),
    IsArrayTest(
        id="decimal128_nan",
        value=DECIMAL128_NAN,
        expected=False,
        msg="Should return false for Decimal128 NaN",
    ),
    IsArrayTest(
        id="decimal128_neg_nan",
        value=Decimal128("-NaN"),
        expected=False,
        msg="Should return false for Decimal128 -NaN",
    ),
    IsArrayTest(
        id="decimal128_inf",
        value=DECIMAL128_INFINITY,
        expected=False,
        msg="Should return false for Decimal128 Infinity",
    ),
    IsArrayTest(
        id="decimal128_neg_inf",
        value=DECIMAL128_NEGATIVE_INFINITY,
        expected=False,
        msg="Should return false for Decimal128 -Infinity",
    ),
    IsArrayTest(
        id="decimal128_neg_zero",
        value=DECIMAL128_NEGATIVE_ZERO,
        expected=False,
        msg="Should return false for Decimal128 -0",
    ),
]

# ---------------------------------------------------------------------------
# Boundary values → false
# ---------------------------------------------------------------------------
BOUNDARY_TESTS: list[IsArrayTest] = [
    IsArrayTest(
        id="int32_max", value=INT32_MAX, expected=False, msg="Should return false for INT32_MAX"
    ),
    IsArrayTest(
        id="int32_min", value=INT32_MIN, expected=False, msg="Should return false for INT32_MIN"
    ),
    IsArrayTest(
        id="int64_max", value=INT64_MAX, expected=False, msg="Should return false for INT64_MAX"
    ),
    IsArrayTest(
        id="int64_min", value=INT64_MIN, expected=False, msg="Should return false for INT64_MIN"
    ),
    IsArrayTest(
        id="decimal128_max",
        value=DECIMAL128_MAX,
        expected=False,
        msg="Should return false for DECIMAL128_MAX",
    ),
    IsArrayTest(
        id="decimal128_min",
        value=DECIMAL128_MIN,
        expected=False,
        msg="Should return false for DECIMAL128_MIN",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_BSON_TESTS = BSON_ARRAY_TRUE_TESTS + BSON_FALSE_TESTS + SPECIAL_NUMERIC_TESTS + BOUNDARY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_BSON_TESTS))
def test_isArray_bson_insert(collection, test):
    """Test $isArray BSON types with values from inserted documents."""
    result = execute_expression_with_insert(collection, {"$isArray": "$val"}, {"val": test.value})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


TEST_SUBSET_FOR_LITERAL = [
    BSON_ARRAY_TRUE_TESTS[0],  # bindata_array
    BSON_ARRAY_TRUE_TESTS[-1],  # nested_mixed_bson_array
    BSON_FALSE_TESTS[0],  # int64
    SPECIAL_NUMERIC_TESTS[0],  # nan
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_isArray_bson_literal(collection, test):
    """Test $isArray BSON types with literal values."""
    expr = {"$literal": test.value} if isinstance(test.value, list) else test.value
    result = execute_expression(collection, {"$isArray": [expr]})
    assert_expression_result(result, expected=test.expected, msg=test.msg)
