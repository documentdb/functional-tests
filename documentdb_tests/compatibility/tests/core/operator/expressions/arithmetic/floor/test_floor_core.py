"""Tests for $floor core flooring behavior across integer, double, and decimal128 inputs."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    INT64_ZERO,
)

# Property [Integer Identity]: floor returns integer inputs unchanged, preserving int/long type.
FLOOR_INTEGER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "identity_positive_int32",
        doc={"value": 1},
        expression={"$floor": ["$value"]},
        expected=1,
        msg="$floor should return a positive int32 unchanged",
    ),
    ExpressionTestCase(
        "identity_negative_int32",
        doc={"value": -1},
        expression={"$floor": ["$value"]},
        expected=-1,
        msg="$floor should return a negative int32 unchanged",
    ),
    ExpressionTestCase(
        "identity_zero_int32",
        doc={"value": 0},
        expression={"$floor": ["$value"]},
        expected=0,
        msg="$floor should return int32 zero unchanged",
    ),
    ExpressionTestCase(
        "identity_positive_int64",
        doc={"value": Int64(1)},
        expression={"$floor": ["$value"]},
        expected=Int64(1),
        msg="$floor should return a positive int64 unchanged",
    ),
    ExpressionTestCase(
        "identity_negative_int64",
        doc={"value": Int64(-1)},
        expression={"$floor": ["$value"]},
        expected=Int64(-1),
        msg="$floor should return a negative int64 unchanged",
    ),
    ExpressionTestCase(
        "identity_zero_int64",
        doc={"value": INT64_ZERO},
        expression={"$floor": ["$value"]},
        expected=INT64_ZERO,
        msg="$floor should return int64 zero unchanged",
    ),
]

# Property [Double Flooring]: floor rounds a double down to the nearest integer, returning a double.
FLOOR_DOUBLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_positive",
        doc={"value": 1.5},
        expression={"$floor": ["$value"]},
        expected=1.0,
        msg="$floor should round a positive double down",
    ),
    ExpressionTestCase(
        "double_negative",
        doc={"value": -1.5},
        expression={"$floor": ["$value"]},
        expected=-2.0,
        msg="$floor should round a negative double down, away from zero",
    ),
    ExpressionTestCase(
        "double_zero",
        doc={"value": DOUBLE_ZERO},
        expression={"$floor": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$floor should return double zero unchanged",
    ),
    ExpressionTestCase(
        "double_negative_zero",
        doc={"value": DOUBLE_NEGATIVE_ZERO},
        expression={"$floor": ["$value"]},
        expected=DOUBLE_NEGATIVE_ZERO,
        msg="$floor should preserve negative zero for a double",
    ),
]

# Property [Decimal Flooring]: floor rounds a decimal128 down, returning decimal128.
FLOOR_DECIMAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_positive_fraction",
        doc={"value": DECIMAL128_ONE_AND_HALF},
        expression={"$floor": ["$value"]},
        expected=Decimal128("1"),
        msg="$floor should round a positive decimal128 down",
    ),
    ExpressionTestCase(
        "decimal_negative_fraction",
        doc={"value": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        expression={"$floor": ["$value"]},
        expected=Decimal128("-2"),
        msg="$floor should round a negative decimal128 down, away from zero",
    ),
    ExpressionTestCase(
        "decimal_whole",
        doc={"value": Decimal128("1")},
        expression={"$floor": ["$value"]},
        expected=Decimal128("1"),
        msg="$floor should return a whole decimal128 unchanged",
    ),
    ExpressionTestCase(
        "decimal_zero",
        doc={"value": DECIMAL128_ZERO},
        expression={"$floor": ["$value"]},
        expected=DECIMAL128_ZERO,
        msg="$floor should return decimal128 zero unchanged",
    ),
    ExpressionTestCase(
        "decimal_negative_zero",
        doc={"value": DECIMAL128_NEGATIVE_ZERO},
        expression={"$floor": ["$value"]},
        expected=DECIMAL128_NEGATIVE_ZERO,
        msg="$floor should preserve negative zero for a decimal128",
    ),
]

FLOOR_CORE_TESTS = FLOOR_INTEGER_TESTS + FLOOR_DOUBLE_TESTS + FLOOR_DECIMAL_TESTS


@pytest.mark.parametrize("test", pytest_params(FLOOR_CORE_TESTS))
def test_floor_core(collection, test):
    """Test $floor core flooring behavior."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


def test_floor_nested_expression(collection):
    """Test $floor accepts an expression as its input."""
    result = execute_expression(collection, {"$floor": {"$floor": -4.1}})
    assert_expression_result(result, expected=-5.0, msg="$floor should evaluate a nested $floor")
