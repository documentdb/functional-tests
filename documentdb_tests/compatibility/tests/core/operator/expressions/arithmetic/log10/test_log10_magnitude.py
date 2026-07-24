"""Tests for $log10 core base-ten logarithm values across sign and numeric type."""

import math

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
from documentdb_tests.framework.test_constants import DECIMAL128_ZERO, DOUBLE_ZERO

# Property [Identity]: $log10 of one is zero for every numeric type.
LOG10_ONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "one_int32",
        doc={"value": 1},
        expression={"$log10": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$log10 should return zero for int32 one",
    ),
    ExpressionTestCase(
        "one_int64",
        doc={"value": Int64(1)},
        expression={"$log10": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$log10 should return zero for int64 one",
    ),
    ExpressionTestCase(
        "one_double",
        doc={"value": 1.0},
        expression={"$log10": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$log10 should return zero for double one",
    ),
    ExpressionTestCase(
        "one_decimal",
        doc={"value": Decimal128("1")},
        expression={"$log10": ["$value"]},
        expected=DECIMAL128_ZERO,
        msg="$log10 should return zero for decimal128 one",
    ),
]

# Property [Positive Powers of Ten]: $log10 of a positive power of ten returns its exact integer
# exponent as a double.
LOG10_POSITIVE_POWER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ten_int32",
        doc={"value": 10},
        expression={"$log10": ["$value"]},
        expected=1.0,
        msg="$log10 should return one for int32 ten",
    ),
    ExpressionTestCase(
        "ten_int64",
        doc={"value": Int64(10)},
        expression={"$log10": ["$value"]},
        expected=1.0,
        msg="$log10 should return one for int64 ten",
    ),
    ExpressionTestCase(
        "ten_double",
        doc={"value": 10.0},
        expression={"$log10": ["$value"]},
        expected=1.0,
        msg="$log10 should return one for double ten",
    ),
    ExpressionTestCase(
        "hundred",
        doc={"value": 100},
        expression={"$log10": ["$value"]},
        expected=2.0,
        msg="$log10 should return two for one hundred",
    ),
    ExpressionTestCase(
        "thousand",
        doc={"value": 1000},
        expression={"$log10": ["$value"]},
        expected=3.0,
        msg="$log10 should return three for one thousand",
    ),
    ExpressionTestCase(
        "ten_thousand",
        doc={"value": 10_000},
        expression={"$log10": ["$value"]},
        expected=4.0,
        msg="$log10 should return four for ten thousand",
    ),
    ExpressionTestCase(
        "million",
        doc={"value": 1_000_000},
        expression={"$log10": ["$value"]},
        expected=6.0,
        msg="$log10 should return six for one million",
    ),
    ExpressionTestCase(
        "billion",
        doc={"value": Int64(1_000_000_000)},
        expression={"$log10": ["$value"]},
        expected=9.0,
        msg="$log10 should return nine for one billion int64",
    ),
    ExpressionTestCase(
        "ten_billion",
        doc={"value": Int64(10_000_000_000)},
        expression={"$log10": ["$value"]},
        expected=10.0,
        msg="$log10 should return ten for ten billion int64",
    ),
    ExpressionTestCase(
        "quadrillion",
        doc={"value": 1e15},
        expression={"$log10": ["$value"]},
        expected=15.0,
        msg="$log10 should return fifteen for one quadrillion",
    ),
    ExpressionTestCase(
        "hundred_quintillion",
        doc={"value": 1e20},
        expression={"$log10": ["$value"]},
        expected=20.0,
        msg="$log10 should return twenty for one hundred quintillion",
    ),
]

# Property [Negative Powers of Ten]: $log10 of a fractional power of ten returns its exact negative
# integer exponent as a double.
LOG10_NEGATIVE_POWER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tenth",
        doc={"value": 0.1},
        expression={"$log10": ["$value"]},
        expected=-1.0,
        msg="$log10 should return negative one for one tenth",
    ),
    ExpressionTestCase(
        "hundredth",
        doc={"value": 0.01},
        expression={"$log10": ["$value"]},
        expected=-2.0,
        msg="$log10 should return negative two for one hundredth",
    ),
    ExpressionTestCase(
        "thousandth",
        doc={"value": 0.001},
        expression={"$log10": ["$value"]},
        expected=-3.0,
        msg="$log10 should return negative three for one thousandth",
    ),
    ExpressionTestCase(
        "ten_thousandth",
        doc={"value": 0.0001},
        expression={"$log10": ["$value"]},
        expected=-4.0,
        msg="$log10 should return negative four for one ten-thousandth",
    ),
    ExpressionTestCase(
        "hundred_thousandth",
        doc={"value": 1e-5},
        expression={"$log10": ["$value"]},
        expected=-5.0,
        msg="$log10 should return negative five for one hundred-thousandth",
    ),
    ExpressionTestCase(
        "billionth",
        doc={"value": 1e-9},
        expression={"$log10": ["$value"]},
        expected=-9.0,
        msg="$log10 should return negative nine for one billionth",
    ),
    ExpressionTestCase(
        "ten_billionth",
        doc={"value": 1e-10},
        expression={"$log10": ["$value"]},
        expected=-10.0,
        msg="$log10 should return negative ten for one ten-billionth",
    ),
    ExpressionTestCase(
        "quadrillionth",
        doc={"value": 1e-15},
        expression={"$log10": ["$value"]},
        expected=-15.0,
        msg="$log10 should return negative fifteen for one quadrillionth",
    ),
]

# Property [Non-Power Values]: $log10 of a value that is not a power of ten returns its
# base-ten logarithm.
LOG10_NON_POWER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "two",
        doc={"value": 2},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(0.3010299956639812),
        msg="$log10 should return the base-ten log of two",
    ),
    ExpressionTestCase(
        "five",
        doc={"value": 5},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(0.6989700043360189),
        msg="$log10 should return the base-ten log of five",
    ),
    ExpressionTestCase(
        "seven",
        doc={"value": 7},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(0.8450980400142568),
        msg="$log10 should return the base-ten log of seven",
    ),
    ExpressionTestCase(
        "fifty",
        doc={"value": 50},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(1.6989700043360187),
        msg="$log10 should return the base-ten log of fifty",
    ),
    ExpressionTestCase(
        "five_hundred",
        doc={"value": 500},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(2.6989700043360187),
        msg="$log10 should return the base-ten log of five hundred",
    ),
    ExpressionTestCase(
        "five_billionth",
        doc={"value": 0.000000005},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(-8.301029995663981),
        msg="$log10 should return the base-ten log of five billionths",
    ),
    ExpressionTestCase(
        "half",
        doc={"value": 0.5},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(-0.3010299956639812),
        msg="$log10 should return the base-ten log of one half",
    ),
    ExpressionTestCase(
        "quarter",
        doc={"value": 0.25},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(-0.6020599913279624),
        msg="$log10 should return the base-ten log of one quarter",
    ),
    ExpressionTestCase(
        "one_and_half",
        doc={"value": 1.5},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(0.17609125905568124),
        msg="$log10 should return the base-ten log of one and a half",
    ),
    ExpressionTestCase(
        "two_and_half",
        doc={"value": 2.5},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(0.3979400086720376),
        msg="$log10 should return the base-ten log of two and a half",
    ),
    ExpressionTestCase(
        "pi",
        doc={"value": math.pi},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(0.4971498726941338),
        msg="$log10 should return the base-ten log of pi",
    ),
    ExpressionTestCase(
        "e",
        doc={"value": math.e},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(0.4342944819032518),
        msg="$log10 should return the base-ten log of e",
    ),
    ExpressionTestCase(
        "e_squared",
        doc={"value": math.e**2},
        expression={"$log10": ["$value"]},
        expected=pytest.approx(0.8685889638065036),
        msg="$log10 should return the base-ten log of e squared",
    ),
]

# Property [Decimal Precision]: $log10 of a decimal128 input returns a full-precision decimal128.
LOG10_DECIMAL_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_ten",
        doc={"value": Decimal128("10")},
        expression={"$log10": ["$value"]},
        expected=Decimal128("1"),
        msg="$log10 should return one as a decimal128 for decimal128 ten",
    ),
    ExpressionTestCase(
        "decimal_hundred",
        doc={"value": Decimal128("100")},
        expression={"$log10": ["$value"]},
        expected=Decimal128("2"),
        msg="$log10 should return two as a decimal128 for decimal128 one hundred",
    ),
    ExpressionTestCase(
        "decimal_two",
        doc={"value": Decimal128("2")},
        expression={"$log10": ["$value"]},
        expected=Decimal128("0.3010299956639811952137388947244930"),
        msg="$log10 should return a full-precision decimal128 for decimal128 two",
    ),
]

LOG10_MAGNITUDE_ALL_TESTS = (
    LOG10_ONE_TESTS
    + LOG10_POSITIVE_POWER_TESTS
    + LOG10_NEGATIVE_POWER_TESTS
    + LOG10_NON_POWER_TESTS
    + LOG10_DECIMAL_PRECISION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LOG10_MAGNITUDE_ALL_TESTS))
def test_log10_magnitude(collection, test_case: ExpressionTestCase):
    """Test $log10 base-ten logarithm value cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
