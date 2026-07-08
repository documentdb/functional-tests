"""Tests for $ceil basic numeric rounding across int32, int64, double, and decimal128 types."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
)

# Property [Integer Identity]: $ceil of any integer value returns the same integer unchanged.
CEIL_INTEGER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "positive_int32",
        doc={"value": 1},
        expression={"$ceil": ["$value"]},
        expected=1,
        msg="$ceil should return the same value for a positive int32",
    ),
    ExpressionTestCase(
        "negative_int32",
        doc={"value": -1},
        expression={"$ceil": ["$value"]},
        expected=-1,
        msg="$ceil should return the same value for a negative int32",
    ),
    ExpressionTestCase(
        "zero_int32",
        doc={"value": 0},
        expression={"$ceil": ["$value"]},
        expected=0,
        msg="$ceil should return zero for int32 zero",
    ),
    ExpressionTestCase(
        "positive_int64",
        doc={"value": Int64(1)},
        expression={"$ceil": ["$value"]},
        expected=Int64(1),
        msg="$ceil should return the same value for a positive int64",
    ),
    ExpressionTestCase(
        "negative_int64",
        doc={"value": Int64(-1)},
        expression={"$ceil": ["$value"]},
        expected=Int64(-1),
        msg="$ceil should return the same value for a negative int64",
    ),
    ExpressionTestCase(
        "zero_int64",
        doc={"value": Int64(0)},
        expression={"$ceil": ["$value"]},
        expected=Int64(0),
        msg="$ceil should return zero for int64 zero",
    ),
]

# Property [Double Rounding]: $ceil rounds a double up to the nearest integer double.
CEIL_DOUBLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "positive_double",
        doc={"value": 1.5},
        expression={"$ceil": ["$value"]},
        expected=2.0,
        msg="$ceil should round up a positive double to the next integer",
    ),
    ExpressionTestCase(
        "negative_double",
        doc={"value": -1.5},
        expression={"$ceil": ["$value"]},
        expected=-1.0,
        msg="$ceil should round a negative double toward zero",
    ),
    ExpressionTestCase(
        "zero_double",
        doc={"value": 0.0},
        expression={"$ceil": ["$value"]},
        expected=0.0,
        msg="$ceil should return zero for double zero",
    ),
    ExpressionTestCase(
        "negative_zero_double",
        doc={"value": DOUBLE_NEGATIVE_ZERO},
        expression={"$ceil": ["$value"]},
        expected=DOUBLE_NEGATIVE_ZERO,
        msg="$ceil should return zero for negative zero double",
    ),
    ExpressionTestCase(
        "negative_fraction",
        doc={"value": -0.5},
        expression={"$ceil": ["$value"]},
        expected=-0.0,
        msg="$ceil should round a negative double fraction up to negative zero",
    ),
]

# Property [Decimal128 Rounding]: $ceil rounds a decimal128 up to the nearest integer decimal128.
CEIL_DECIMAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "positive_decimal",
        doc={"value": Decimal128("1")},
        expression={"$ceil": ["$value"]},
        expected=Decimal128("1"),
        msg="$ceil should return the same value for a positive whole decimal128",
    ),
    ExpressionTestCase(
        "negative_decimal",
        doc={"value": Decimal128("-1")},
        expression={"$ceil": ["$value"]},
        expected=Decimal128("-1"),
        msg="$ceil should return the same value for a negative whole decimal128",
    ),
    ExpressionTestCase(
        "zero_decimal",
        doc={"value": Decimal128("0")},
        expression={"$ceil": ["$value"]},
        expected=Decimal128("0"),
        msg="$ceil should return zero for decimal128 zero",
    ),
    ExpressionTestCase(
        "negative_zero_decimal",
        doc={"value": DECIMAL128_NEGATIVE_ZERO},
        expression={"$ceil": ["$value"]},
        expected=DECIMAL128_NEGATIVE_ZERO,
        msg="$ceil should return negative zero for negative zero decimal128",
    ),
    ExpressionTestCase(
        "positive_decimal_fraction",
        doc={"value": Decimal128("1.5")},
        expression={"$ceil": ["$value"]},
        expected=Decimal128("2"),
        msg="$ceil should round up a positive decimal128 fraction",
    ),
    ExpressionTestCase(
        "negative_decimal_fraction",
        doc={"value": Decimal128("-1.5")},
        expression={"$ceil": ["$value"]},
        expected=Decimal128("-1"),
        msg="$ceil should round a negative decimal128 fraction toward zero",
    ),
]

CEIL_NUMERIC_ALL_TESTS = CEIL_INTEGER_TESTS + CEIL_DOUBLE_TESTS + CEIL_DECIMAL_TESTS


@pytest.mark.parametrize("test_case", pytest_params(CEIL_NUMERIC_ALL_TESTS))
def test_ceil_numeric(collection, test_case: ExpressionTestCase):
    """Test $ceil basic numeric rounding for integer, double, and decimal128 inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
