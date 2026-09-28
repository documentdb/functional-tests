"""Tests for $ln core natural-logarithm values across sign and numeric type."""

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

# Property [Identity]: $ln of one is zero for every numeric type.
LN_ONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "one_int32",
        doc={"value": 1},
        expression={"$ln": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$ln should return zero for int32 one",
    ),
    ExpressionTestCase(
        "one_int64",
        doc={"value": Int64(1)},
        expression={"$ln": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$ln should return zero for int64 one",
    ),
    ExpressionTestCase(
        "one_double",
        doc={"value": 1.0},
        expression={"$ln": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$ln should return zero for double one",
    ),
    ExpressionTestCase(
        "one_decimal",
        doc={"value": Decimal128("1")},
        expression={"$ln": ["$value"]},
        expected=DECIMAL128_ZERO,
        msg="$ln should return zero for decimal128 one",
    ),
]

# Property [Value Above One]: $ln returns a positive natural logarithm for inputs greater than one.
LN_ABOVE_ONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "e_double",
        doc={"value": math.e},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(1.0),
        msg="$ln should return one for e",
    ),
    ExpressionTestCase(
        "e_squared",
        doc={"value": math.e**2},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(2.0),
        msg="$ln should return two for e squared",
    ),
    ExpressionTestCase(
        "two",
        doc={"value": 2},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(0.6931471805599453),
        msg="$ln should return the natural log of two",
    ),
    ExpressionTestCase(
        "ten",
        doc={"value": 10},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(2.302585092994046),
        msg="$ln should return the natural log of ten",
    ),
    ExpressionTestCase(
        "hundred",
        doc={"value": 100},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(4.605170185988092),
        msg="$ln should return the natural log of one hundred",
    ),
    ExpressionTestCase(
        "thousand",
        doc={"value": 1000},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(6.907755278982137),
        msg="$ln should return the natural log of one thousand",
    ),
    ExpressionTestCase(
        "million",
        doc={"value": 1_000_000},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(13.815510557964274),
        msg="$ln should return the natural log of one million",
    ),
    ExpressionTestCase(
        "billion",
        doc={"value": Int64(1_000_000_000)},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(20.72326583694641),
        msg="$ln should return the natural log of one billion int64",
    ),
    ExpressionTestCase(
        "one_and_half",
        doc={"value": 1.5},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(0.4054651081081644),
        msg="$ln should return the natural log of one and a half",
    ),
    ExpressionTestCase(
        "two_and_half",
        doc={"value": 2.5},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(0.9162907318741551),
        msg="$ln should return the natural log of two and a half",
    ),
    ExpressionTestCase(
        "pi",
        doc={"value": math.pi},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(1.1447298858494002),
        msg="$ln should return the natural log of pi",
    ),
]

# Property [Value Below One]: $ln returns a negative natural logarithm for inputs between zero and
# one.
LN_BELOW_ONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "half",
        doc={"value": 0.5},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(-0.6931471805599453),
        msg="$ln should return the natural log of one half",
    ),
    ExpressionTestCase(
        "tenth",
        doc={"value": 0.1},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(-2.302585092994046),
        msg="$ln should return the natural log of one tenth",
    ),
    ExpressionTestCase(
        "hundredth",
        doc={"value": 0.01},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(-4.605170185988091),
        msg="$ln should return the natural log of one hundredth",
    ),
    ExpressionTestCase(
        "thousandth",
        doc={"value": 0.001},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(-6.907755278982137),
        msg="$ln should return the natural log of one thousandth",
    ),
    ExpressionTestCase(
        "ten_thousandth",
        doc={"value": 0.0001},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(-9.210340371976182),
        msg="$ln should return the natural log of one ten-thousandth",
    ),
    ExpressionTestCase(
        "billionth",
        doc={"value": 0.000000001},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(-20.72326583694641),
        msg="$ln should return the natural log of one billionth",
    ),
    ExpressionTestCase(
        "five_billionth",
        doc={"value": 0.000000005},
        expression={"$ln": ["$value"]},
        expected=pytest.approx(-19.11382792451231),
        msg="$ln should return the natural log of five billionths",
    ),
]

# Property [Decimal Precision]: $ln of a decimal128 input returns a full-precision decimal128.
LN_DECIMAL_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_e",
        doc={"value": Decimal128("2.718281828459045")},
        expression={"$ln": ["$value"]},
        expected=Decimal128("0.9999999999999999134157889710887611"),
        msg="$ln should return a full-precision decimal128 near one for a decimal128 near e",
    ),
    ExpressionTestCase(
        "decimal_ten",
        doc={"value": Decimal128("10")},
        expression={"$ln": ["$value"]},
        expected=Decimal128("2.302585092994045684017991454684364"),
        msg="$ln should return a full-precision decimal128 for decimal128 ten",
    ),
]

LN_MAGNITUDE_ALL_TESTS = (
    LN_ONE_TESTS + LN_ABOVE_ONE_TESTS + LN_BELOW_ONE_TESTS + LN_DECIMAL_PRECISION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LN_MAGNITUDE_ALL_TESTS))
def test_ln_magnitude(collection, test_case: ExpressionTestCase):
    """Test $ln natural-logarithm value cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
