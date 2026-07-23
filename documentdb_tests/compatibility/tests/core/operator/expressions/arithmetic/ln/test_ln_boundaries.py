"""Tests for $ln at representable-range boundaries, including subnormal and extreme inputs."""

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

# Property [Integer Boundaries]: $ln of the largest representable integers returns a finite double.
LN_INTEGER_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max",
        doc={"value": INT32_MAX},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(21.487562596892644),
        msg="$ln should return the natural log of INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_max_minus_1",
        doc={"value": INT32_MAX_MINUS_1},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(21.487562596426983),
        msg="$ln should return the natural log of INT32_MAX minus one",
    ),
    ExpressionTestCase(
        "int64_max",
        doc={"value": INT64_MAX},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(43.66827237527655),
        msg="$ln should return the natural log of INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_max_minus_1",
        doc={"value": INT64_MAX_MINUS_1},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(43.66827237527655),
        msg="$ln should return the natural log of INT64_MAX minus one",
    ),
]

# Property [Double Boundaries]: $ln at the double subnormal and near-limit range returns the
# expected large-magnitude values.
LN_DOUBLE_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_min_subnormal",
        doc={"value": DOUBLE_MIN_SUBNORMAL},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(-744.4400719213812),
        msg="$ln should return a large negative value for the minimum subnormal double",
    ),
    ExpressionTestCase(
        "double_near_min",
        doc={"value": DOUBLE_NEAR_MIN},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(-709.1962086421661),
        msg="$ln should return a large negative value for a near-zero positive double",
    ),
    ExpressionTestCase(
        "double_near_max",
        doc={"value": DOUBLE_NEAR_MAX},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(709.1962086421661),
        msg="$ln should return a large positive value for a near-maximum double",
    ),
    ExpressionTestCase(
        "double_max_safe_integer",
        doc={"value": DOUBLE_MAX_SAFE_INTEGER},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(36.7368005696771),
        msg="$ln should return the natural log of the maximum safe integer double",
    ),
    ExpressionTestCase(
        "double_precision_loss",
        doc={"value": DOUBLE_PRECISION_LOSS},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(36.7368005696771),
        msg="$ln should return the same value as the maximum safe integer for the next "
        "integer double, which is not representable",
    ),
    ExpressionTestCase(
        "very_small_positive",
        doc={"value": 1e-300},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(-690.7755278982137),
        msg="$ln should return a large negative value for a very small positive double",
    ),
]

# Property [Decimal128 Boundaries]: $ln of extreme decimal128 exponents returns a full-precision
# decimal128 result.
LN_DECIMAL_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_small_exponent",
        doc={"value": DECIMAL128_SMALL_EXPONENT},
        expression={"$ln": ["$value"]},
        expected=Decimal128("-14144.78022626242263692252150612605"),
        msg="$ln should return a large negative decimal128 for a decimal128 with a small exponent",
    ),
    ExpressionTestCase(
        "decimal_min_positive",
        doc={"value": DECIMAL128_MIN_POSITIVE},
        expression={"$ln": ["$value"]},
        expected=Decimal128("-14220.76553433122614449511522413063"),
        msg="$ln should return a large negative decimal128 for the smallest positive decimal128",
    ),
    ExpressionTestCase(
        "decimal_max",
        doc={"value": DECIMAL128_MAX},
        expression={"$ln": ["$value"]},
        expected=Decimal128("14149.38539644841072829055748903542"),
        msg="$ln should return a large positive decimal128 for the maximum decimal128",
    ),
    ExpressionTestCase(
        "decimal_trailing_zero",
        doc={"value": DECIMAL128_TRAILING_ZERO},
        expression={"$ln": ["$value"]},
        expected=DECIMAL128_ZERO,
        msg="$ln should return zero for a decimal128 one with a trailing zero",
    ),
]

LN_BOUNDARY_ALL_TESTS = (
    LN_INTEGER_BOUNDARY_TESTS + LN_DOUBLE_BOUNDARY_TESTS + LN_DECIMAL_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LN_BOUNDARY_ALL_TESTS))
def test_ln_boundaries(collection, test_case: ExpressionTestCase):
    """Test $ln representable-range boundary cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
