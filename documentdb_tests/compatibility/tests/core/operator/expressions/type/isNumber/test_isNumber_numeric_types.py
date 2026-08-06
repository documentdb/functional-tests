"""Tests for $isNumber with numeric BSON types (int32, int64, double, Decimal128)."""

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT32_ZERO,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

pytestmark = pytest.mark.aggregate


@dataclass(frozen=True)
class IsNumberTest(BaseTestCase):
    value: Any = None


# Property [Numeric Types]: $isNumber returns true for all numeric BSON types.
NUMERIC_TYPE_TESTS: list[IsNumberTest] = [
    # int32
    IsNumberTest(
        "int32_zero", value=INT32_ZERO, expected=True, msg="Should return true for int32 zero"
    ),
    IsNumberTest(
        "int32_positive", value=42, expected=True, msg="Should return true for positive int32"
    ),
    IsNumberTest(
        "int32_negative", value=-1, expected=True, msg="Should return true for negative int32"
    ),
    IsNumberTest(
        "int32_max", value=INT32_MAX, expected=True, msg="Should return true for int32 max"
    ),
    IsNumberTest(
        "int32_min", value=INT32_MIN, expected=True, msg="Should return true for int32 min"
    ),
    # int64
    IsNumberTest(
        "int64_zero", value=INT64_ZERO, expected=True, msg="Should return true for int64 zero"
    ),
    IsNumberTest(
        "int64_positive",
        value=Int64(100),
        expected=True,
        msg="Should return true for positive int64",
    ),
    IsNumberTest(
        "int64_negative",
        value=Int64(-100),
        expected=True,
        msg="Should return true for negative int64",
    ),
    IsNumberTest(
        "int64_max", value=INT64_MAX, expected=True, msg="Should return true for int64 max"
    ),
    IsNumberTest(
        "int64_min", value=INT64_MIN, expected=True, msg="Should return true for int64 min"
    ),
    # double
    IsNumberTest("double_zero", value=0.0, expected=True, msg="Should return true for double zero"),
    IsNumberTest(
        "double_positive", value=3.14, expected=True, msg="Should return true for positive double"
    ),
    IsNumberTest(
        "double_negative", value=-2.71, expected=True, msg="Should return true for negative double"
    ),
    IsNumberTest(
        "double_negative_zero",
        value=DOUBLE_NEGATIVE_ZERO,
        expected=True,
        msg="Should return true for double negative zero",
    ),
    IsNumberTest(
        "double_nan",
        value=FLOAT_NAN,
        expected=True,
        msg="Should return true for double NaN (numeric type)",
    ),
    IsNumberTest(
        "double_infinity",
        value=FLOAT_INFINITY,
        expected=True,
        msg="Should return true for double Infinity (numeric type)",
    ),
    IsNumberTest(
        "double_neg_infinity",
        value=FLOAT_NEGATIVE_INFINITY,
        expected=True,
        msg="Should return true for double negative Infinity (numeric type)",
    ),
    # Decimal128
    IsNumberTest(
        "decimal128_zero",
        value=DECIMAL128_ZERO,
        expected=True,
        msg="Should return true for Decimal128 zero",
    ),
    IsNumberTest(
        "decimal128_positive",
        value=Decimal128("1.5"),
        expected=True,
        msg="Should return true for positive Decimal128",
    ),
    IsNumberTest(
        "decimal128_negative",
        value=Decimal128("-1.5"),
        expected=True,
        msg="Should return true for negative Decimal128",
    ),
    IsNumberTest(
        "decimal128_negative_zero",
        value=DECIMAL128_NEGATIVE_ZERO,
        expected=True,
        msg="Should return true for Decimal128 negative zero",
    ),
    IsNumberTest(
        "decimal128_nan",
        value=DECIMAL128_NAN,
        expected=True,
        msg="Should return true for Decimal128 NaN (numeric type)",
    ),
    IsNumberTest(
        "decimal128_infinity",
        value=DECIMAL128_INFINITY,
        expected=True,
        msg="Should return true for Decimal128 Infinity (numeric type)",
    ),
    IsNumberTest(
        "decimal128_neg_infinity",
        value=DECIMAL128_NEGATIVE_INFINITY,
        expected=True,
        msg="Should return true for Decimal128 negative Infinity (numeric type)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NUMERIC_TYPE_TESTS))
def test_isNumber_numeric_literal(collection, test):
    """Test $isNumber returns true for numeric BSON type literals."""
    result = execute_expression(collection, {"$isNumber": test.value})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(NUMERIC_TYPE_TESTS))
def test_isNumber_numeric_field(collection, test):
    """Test $isNumber returns true when referencing a document field with a numeric value."""
    result = execute_expression_with_insert(
        collection, {"$isNumber": "$value"}, {"value": test.value}
    )
    assert_expression_result(result, expected=test.expected, msg=test.msg)
