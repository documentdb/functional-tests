"""Tests for $abs magnitude across numeric types and signed-zero handling."""

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
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    INT64_ZERO,
)

# Property [Magnitude]: $abs returns the absolute value of a number, preserving its numeric type.
ABS_MAGNITUDE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "positive_int32",
        doc={"value": 1},
        expression={"$abs": ["$value"]},
        expected=1,
        msg="$abs should return the same value for a positive int32",
    ),
    ExpressionTestCase(
        "negative_int32",
        doc={"value": -1},
        expression={"$abs": ["$value"]},
        expected=1,
        msg="$abs should return the positive value for a negative int32",
    ),
    ExpressionTestCase(
        "positive_int64",
        doc={"value": Int64(1)},
        expression={"$abs": ["$value"]},
        expected=Int64(1),
        msg="$abs should return the same value for a positive int64",
    ),
    ExpressionTestCase(
        "negative_int64",
        doc={"value": Int64(-1)},
        expression={"$abs": ["$value"]},
        expected=Int64(1),
        msg="$abs should return the positive value for a negative int64",
    ),
    ExpressionTestCase(
        "positive_double",
        doc={"value": 1.5},
        expression={"$abs": ["$value"]},
        expected=1.5,
        msg="$abs should return the same value for a positive double",
    ),
    ExpressionTestCase(
        "negative_double",
        doc={"value": -1.5},
        expression={"$abs": ["$value"]},
        expected=1.5,
        msg="$abs should return the positive value for a negative double",
    ),
    ExpressionTestCase(
        "positive_decimal",
        doc={"value": Decimal128("1")},
        expression={"$abs": ["$value"]},
        expected=Decimal128("1"),
        msg="$abs should return the same value for a positive decimal128",
    ),
    ExpressionTestCase(
        "negative_decimal",
        doc={"value": Decimal128("-1")},
        expression={"$abs": ["$value"]},
        expected=Decimal128("1"),
        msg="$abs should return the positive value for a negative decimal128",
    ),
]

# Property [Zero]: $abs of positive or negative zero returns positive zero for each numeric type.
ABS_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_int32",
        doc={"value": 0},
        expression={"$abs": ["$value"]},
        expected=0,
        msg="$abs should return zero for int32 zero",
    ),
    ExpressionTestCase(
        "zero_int64",
        doc={"value": INT64_ZERO},
        expression={"$abs": ["$value"]},
        expected=INT64_ZERO,
        msg="$abs should return zero for int64 zero",
    ),
    ExpressionTestCase(
        "zero_double",
        doc={"value": DOUBLE_ZERO},
        expression={"$abs": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$abs should return zero for double zero",
    ),
    ExpressionTestCase(
        "negative_zero_double",
        doc={"value": DOUBLE_NEGATIVE_ZERO},
        expression={"$abs": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$abs should return positive zero for negative zero double",
    ),
    ExpressionTestCase(
        "zero_decimal",
        doc={"value": DECIMAL128_ZERO},
        expression={"$abs": ["$value"]},
        expected=DECIMAL128_ZERO,
        msg="$abs should return zero for decimal128 zero",
    ),
    ExpressionTestCase(
        "negative_zero_decimal",
        doc={"value": DECIMAL128_NEGATIVE_ZERO},
        expression={"$abs": ["$value"]},
        expected=DECIMAL128_ZERO,
        msg="$abs should return positive zero for negative zero decimal128",
    ),
]

ABS_MAGNITUDE_ALL_TESTS = ABS_MAGNITUDE_TESTS + ABS_ZERO_TESTS


@pytest.mark.parametrize("test_case", pytest_params(ABS_MAGNITUDE_ALL_TESTS))
def test_abs_magnitude(collection, test_case: ExpressionTestCase):
    """Test $abs magnitude and signed-zero cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
