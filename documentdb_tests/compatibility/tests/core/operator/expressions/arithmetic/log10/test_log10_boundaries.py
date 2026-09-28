"""Tests for $log10 at representable-range boundaries, including subnormal and extreme inputs."""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_MAX,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_PRECISION_LOSS,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT64_MAX,
    INT64_MAX_MINUS_1,
)

# Property [Integer Boundaries]: $log10 of the largest representable integers returns a finite
# double.
LOG10_INTEGER_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max",
        doc={"value": INT32_MAX},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(9.331929865381182),
        msg="$log10 should return the base-ten log of INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_max_minus_1",
        doc={"value": INT32_MAX_MINUS_1},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(9.33192986517895),
        msg="$log10 should return the base-ten log of INT32_MAX minus one",
    ),
    ExpressionTestCase(
        "int64_max",
        doc={"value": INT64_MAX},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(18.964889726830815),
        msg="$log10 should return the base-ten log of INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_max_minus_1",
        doc={"value": INT64_MAX_MINUS_1},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(18.964889726830815),
        msg="$log10 should return the base-ten log of INT64_MAX minus one",
    ),
]

# Property [Double Boundaries]: $log10 at the double subnormal and near-limit range returns the
# expected large-magnitude values.
LOG10_DOUBLE_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_min_subnormal",
        doc={"value": DOUBLE_MIN_SUBNORMAL},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(-323.3062153431158),
        msg="$log10 should return a large negative value for the minimum subnormal double",
    ),
    ExpressionTestCase(
        "double_near_min",
        doc={"value": DOUBLE_NEAR_MIN},
        expression={"$log10": ["$value"]},
        expected=-308.0,
        msg="$log10 should return negative three hundred eight for a near-zero positive double",
    ),
    ExpressionTestCase(
        "double_near_max",
        doc={"value": DOUBLE_NEAR_MAX},
        expression={"$log10": ["$value"]},
        expected=308.0,
        msg="$log10 should return three hundred eight for a near-maximum double",
    ),
    ExpressionTestCase(
        "double_max_safe_integer",
        doc={"value": DOUBLE_MAX_SAFE_INTEGER},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(15.954589770191003),
        msg="$log10 should return the base-ten log of the maximum safe integer double",
    ),
    ExpressionTestCase(
        "double_precision_loss",
        doc={"value": DOUBLE_PRECISION_LOSS},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(15.954589770191003),
        msg="$log10 should return the same value as the maximum safe integer for the next "
        "integer double, which is not representable",
    ),
    ExpressionTestCase(
        "very_small_positive",
        doc={"value": 1e-300},
        expression={"$log10": ["$value"]},
        expected=-300.0,
        msg="$log10 should return negative three hundred for a very small positive double",
    ),
]

# Property [Decimal128 Boundaries]: $log10 of extreme decimal128 exponents returns a full-precision
# decimal128 result.
LOG10_DECIMAL_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_small_exponent",
        doc={"value": DECIMAL128_SMALL_EXPONENT},
        expression={"$log10": ["$value"]},
        expected=Decimal128("-6143"),
        msg="$log10 should return the exact negative exponent for a decimal128 with a small "
        "exponent",
    ),
    ExpressionTestCase(
        "decimal_min_positive",
        doc={"value": DECIMAL128_MIN_POSITIVE},
        expression={"$log10": ["$value"]},
        expected=Decimal128("-6176"),
        msg="$log10 should return the exact negative exponent for the smallest positive decimal128",
    ),
    ExpressionTestCase(
        "decimal_max",
        doc={"value": DECIMAL128_MAX},
        expression={"$log10": ["$value"]},
        expected=Decimal128("6145"),
        msg="$log10 should return the exponent for the maximum decimal128",
    ),
    ExpressionTestCase(
        "decimal_trailing_zero",
        doc={"value": DECIMAL128_TRAILING_ZERO},
        expression={"$log10": ["$value"]},
        expected=DECIMAL128_ZERO,
        msg="$log10 should return zero for a decimal128 one with a trailing zero",
    ),
]

LOG10_BOUNDARY_ALL_TESTS = (
    LOG10_INTEGER_BOUNDARY_TESTS + LOG10_DOUBLE_BOUNDARY_TESTS + LOG10_DECIMAL_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LOG10_BOUNDARY_ALL_TESTS))
def test_log10_boundaries(collection, test_case: ExpressionTestCase):
    """Test $log10 representable-range boundary cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
