"""Tests for insert numeric boundary and DatetimeMS preservation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Decimal128
from bson.datetime_ms import DatetimeMS

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import (
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Sentinel: expected value equals the inserted value (most numeric roundtrip cases).
_SAME = object()


@dataclass(frozen=True)
class NumericTest(BaseTestCase):
    """Test case for numeric and DatetimeMS roundtrip preservation."""

    insert_value: Any = None
    # Expected value after retrieval. Use _SAME when expected == insert_value.
    expected_value: Any = _SAME


# Property [Numeric Roundtrip]: insert preserves numeric boundary values for each BSON
# numeric type without type promotion or precision loss. DatetimeMS values are decoded
# as datetime objects with UTC timezone. Negative NaN is tested separately because
# NaN != NaN breaks standard equality comparison.
TESTS: list[NumericTest] = [
    # Int64 boundaries
    NumericTest(
        "int64_min",
        insert_value=INT64_MIN,
        msg="insert should preserve INT64_MIN.",
    ),
    NumericTest(
        "int64_zero",
        insert_value=INT64_ZERO,
        msg="insert should preserve INT64_ZERO.",
    ),
    NumericTest(
        "int64_max",
        insert_value=INT64_MAX,
        msg="insert should preserve INT64_MAX.",
    ),
    # Double boundary and special values
    NumericTest(
        "double_min_negative_subnormal",
        insert_value=DOUBLE_MIN_NEGATIVE_SUBNORMAL,
        msg="insert should preserve the smallest negative subnormal double.",
    ),
    NumericTest(
        "double_negative_zero",
        insert_value=DOUBLE_NEGATIVE_ZERO,
        msg="insert should preserve double negative zero.",
    ),
    NumericTest(
        "double_zero",
        insert_value=DOUBLE_ZERO,
        msg="insert should preserve double zero.",
    ),
    NumericTest(
        "double_min_subnormal",
        insert_value=DOUBLE_MIN_SUBNORMAL,
        msg="insert should preserve the smallest positive subnormal double.",
    ),
    NumericTest(
        "double_near_max",
        insert_value=DOUBLE_NEAR_MAX,
        msg="insert should preserve a large double near the maximum.",
    ),
    NumericTest(
        "double_near_min",
        insert_value=DOUBLE_NEAR_MIN,
        msg="insert should preserve a small double near the minimum positive.",
    ),  # Float special values (Infinity)
    NumericTest(
        "float_negative_infinity",
        insert_value=FLOAT_NEGATIVE_INFINITY,
        msg="insert should preserve negative float Infinity.",
    ),
    NumericTest(
        "float_infinity",
        insert_value=FLOAT_INFINITY,
        msg="insert should preserve float Infinity.",
    ),
    # Decimal128 boundaries and special values
    NumericTest(
        "decimal128_negative_infinity",
        insert_value=DECIMAL128_NEGATIVE_INFINITY,
        msg="insert should preserve Decimal128 negative Infinity.",
    ),
    NumericTest(
        "decimal128_min",
        insert_value=DECIMAL128_MIN,
        msg="insert should preserve Decimal128 minimum value.",
    ),
    NumericTest(
        "decimal128_zero",
        insert_value=DECIMAL128_ZERO,
        msg="insert should preserve Decimal128 zero.",
    ),
    NumericTest(
        "decimal128_negative_zero",
        insert_value=DECIMAL128_NEGATIVE_ZERO,
        msg="insert should preserve Decimal128 negative zero.",
    ),
    NumericTest(
        "decimal128_infinity",
        insert_value=Decimal128("Infinity"),
        msg="insert should preserve Decimal128 positive Infinity.",
    ),
    NumericTest(
        "decimal128_max",
        insert_value=DECIMAL128_MAX,
        msg="insert should preserve Decimal128 maximum value.",
    ),
    NumericTest(
        "decimal128_large_exponent",
        insert_value=DECIMAL128_LARGE_EXPONENT,
        msg="insert should preserve Decimal128 large exponent.",
    ),
    NumericTest(
        "decimal128_small_exponent",
        insert_value=DECIMAL128_SMALL_EXPONENT,
        msg="insert should preserve Decimal128 small exponent.",
    ),
    NumericTest(
        "decimal128_trailing_zero",
        insert_value=DECIMAL128_TRAILING_ZERO,
        msg="insert should preserve Decimal128 trailing zero.",
    ),
    NumericTest(
        "decimal128_many_trailing_zeros",
        insert_value=DECIMAL128_MANY_TRAILING_ZEROS,
        msg="insert should preserve Decimal128 many trailing zeros.",
    ),
    # DatetimeMS roundtrip — insert_value differs from expected_value (driver decodes to datetime)
    NumericTest(
        "datetime_ms_epoch",
        insert_value=DatetimeMS(0),
        expected_value=datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="insert should preserve DatetimeMS epoch as UTC datetime.",
    ),
    NumericTest(
        "datetime_ms_before_epoch",
        insert_value=DatetimeMS(-1),
        expected_value=datetime(1969, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc),
        msg="insert should preserve DatetimeMS before epoch as UTC datetime.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_insert_numeric_and_datetime_boundary(collection, test: NumericTest):
    """Test that insert preserves numeric boundary and DatetimeMS values."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": test.insert_value}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    expected = test.insert_value if test.expected_value is _SAME else test.expected_value
    assertSuccess(result, [{"_id": 1, "value": expected}], msg=test.msg)


# NaN cases require assertSuccessNaN because NaN != NaN breaks standard equality.
@pytest.mark.insert
def test_insert_double_negative_nan(collection):
    """Test that insert preserves negative NaN (double)."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": FLOAT_NEGATIVE_NAN}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccessNaN(
        result, [{"_id": 1, "value": float("nan")}], msg="insert should preserve -NaN (double)."
    )


@pytest.mark.insert
def test_insert_decimal128_negative_nan(collection):
    """Test that insert preserves negative NaN (Decimal128)."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": DECIMAL128_NEGATIVE_NAN}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccessNaN(
        result,
        [{"_id": 1, "value": Decimal128("NaN")}],
        msg="insert should preserve -NaN (Decimal128).",
    )
