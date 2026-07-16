"""Tests for $log at integer, double, and decimal128 representable-range boundaries."""

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
    DECIMAL128_MIN_POSITIVE,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    INT32_MAX,
    INT64_MAX,
)

# Property [Integer Boundaries]: $log of large integers, including the int32 and int64 maxima,
# returns a finite double.
LOG_INTEGER_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "base10_billion",
        doc={"value": Int64(1_000_000_000), "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(9.0),
        msg="$log should return nine for one billion in base ten",
    ),
    ExpressionTestCase(
        "base2_2_to_30",
        doc={"value": Int64(1_073_741_824), "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(30.0),
        msg="$log should return thirty for two to the thirtieth in base two",
    ),
    ExpressionTestCase(
        "base10_max_int32",
        doc={"value": INT32_MAX, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(9.331929865381182),
        msg="$log should return the base ten log of INT32_MAX",
    ),
    ExpressionTestCase(
        "base10_max_int64",
        doc={"value": INT64_MAX, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(18.964889726830812),
        msg="$log should return the base ten log of INT64_MAX",
    ),
    ExpressionTestCase(
        "base2_max_int32",
        doc={"value": INT32_MAX, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(30.999999999328196),
        msg="$log should return the base two log of INT32_MAX",
    ),
    ExpressionTestCase(
        "base2_max_int64",
        doc={"value": INT64_MAX, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(63.0),
        msg="$log should return the base two log of INT64_MAX",
    ),
]

# Property [Double Boundaries]: $log at the double subnormal and near-limit range, in the value and
# base arguments, returns the expected large or small-magnitude result.
LOG_DOUBLE_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "value_min_subnormal",
        doc={"value": DOUBLE_MIN_SUBNORMAL, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-323.30621534311575),
        msg="$log should return a large negative result for the minimum subnormal double value",
    ),
    ExpressionTestCase(
        "value_near_min",
        doc={"value": DOUBLE_NEAR_MIN, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-308.0),
        msg="$log should return negative three hundred eight for a near-zero positive double value",
    ),
    ExpressionTestCase(
        "value_near_max",
        doc={"value": DOUBLE_NEAR_MAX, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(308.0),
        msg="$log should return three hundred eight for a near-maximum double value",
    ),
    ExpressionTestCase(
        "value_very_small_positive",
        doc={"value": 1e-300, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-299.99999999999994),
        msg="$log should return a large negative result for a very small positive double value",
    ),
    ExpressionTestCase(
        "base_near_max",
        doc={"value": 10, "base": DOUBLE_NEAR_MAX},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(0.003246753246753247),
        msg="$log should return a small positive result for a near-maximum double base",
    ),
]

# Property [Decimal Precision]: $log of decimal128 operands returns a full-precision decimal128.
LOG_DECIMAL_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_precision_base10",
        doc={"value": Decimal128("1000"), "base": Decimal128("10")},
        expression={"$log": ["$value", "$base"]},
        expected=Decimal128("3.000000000000000000000000000000000"),
        msg="$log should return a full-precision decimal128 three for one thousand in base ten",
    ),
    ExpressionTestCase(
        "decimal_precision_base2",
        doc={"value": Decimal128("64"), "base": Decimal128("2")},
        expression={"$log": ["$value", "$base"]},
        expected=Decimal128("5.999999999999999999999999999999999"),
        msg="$log should return a full-precision decimal128 near six for sixty-four in base two",
    ),
    ExpressionTestCase(
        "decimal_min_positive_value",
        doc={"value": DECIMAL128_MIN_POSITIVE, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=Decimal128("-6175.999999999999999999999999999999"),
        msg="$log should return a full-precision decimal128 near the exponent for the smallest "
        "positive decimal128 value in base ten",
    ),
]

LOG_BOUNDARY_ALL_TESTS = (
    LOG_INTEGER_BOUNDARY_TESTS + LOG_DOUBLE_BOUNDARY_TESTS + LOG_DECIMAL_PRECISION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LOG_BOUNDARY_ALL_TESTS))
def test_log_boundaries(collection, test_case: ExpressionTestCase):
    """Test $log representable-range boundary cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
