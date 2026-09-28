"""Tests for $log core logarithm values across base, sign, and numeric type."""

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
from documentdb_tests.framework.test_constants import DOUBLE_ZERO

# Property [Identity]: $log of one is zero for any base and numeric type.
LOG_IDENTITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "one_base10",
        doc={"value": 1, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=DOUBLE_ZERO,
        msg="$log should return zero for one in base ten",
    ),
    ExpressionTestCase(
        "one_base2",
        doc={"value": 1, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=DOUBLE_ZERO,
        msg="$log should return zero for one in base two",
    ),
    ExpressionTestCase(
        "one_base5",
        doc={"value": 1, "base": 5},
        expression={"$log": ["$value", "$base"]},
        expected=DOUBLE_ZERO,
        msg="$log should return zero for one in base five",
    ),
]

# Property [Base Equals Value]: $log of a value in its own base is one.
LOG_BASE_EQUALS_VALUE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_ten",
        doc={"value": 10, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(1.0),
        msg="$log should return one when value equals base ten",
    ),
    ExpressionTestCase(
        "same_two",
        doc={"value": 2, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(1.0),
        msg="$log should return one when value equals base two",
    ),
    ExpressionTestCase(
        "same_five",
        doc={"value": 5, "base": 5},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(1.0),
        msg="$log should return one when value equals base five",
    ),
]

# Property [Same Type]: $log of same-typed value and base returns the correct result per type.
LOG_SAME_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "base10_hundred_int32",
        doc={"value": 100, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(2.0),
        msg="$log should return two for one hundred in base ten int32",
    ),
    ExpressionTestCase(
        "base10_thousand_int64",
        doc={"value": Int64(1000), "base": Int64(10)},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(3.0),
        msg="$log should return three for one thousand in base ten int64",
    ),
    ExpressionTestCase(
        "base10_ten_double",
        doc={"value": 10.0, "base": 10.0},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(1.0),
        msg="$log should return one for ten in base ten double",
    ),
    ExpressionTestCase(
        "base10_hundred_decimal",
        doc={"value": Decimal128("100"), "base": Decimal128("10")},
        expression={"$log": ["$value", "$base"]},
        expected=Decimal128("2"),
        msg="$log should return two for one hundred in base ten decimal128",
    ),
    ExpressionTestCase(
        "base2_eight_int32",
        doc={"value": 8, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(3.0),
        msg="$log should return three for eight in base two int32",
    ),
    ExpressionTestCase(
        "base2_1024_int64",
        doc={"value": Int64(1024), "base": Int64(2)},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(10.0),
        msg="$log should return ten for 1024 in base two int64",
    ),
    ExpressionTestCase(
        "base2_sixteen_double",
        doc={"value": 16.0, "base": 2.0},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(4.0),
        msg="$log should return four for sixteen in base two double",
    ),
    ExpressionTestCase(
        "base2_32_decimal",
        doc={"value": Decimal128("32"), "base": Decimal128("2")},
        expression={"$log": ["$value", "$base"]},
        expected=Decimal128("5"),
        msg="$log should return five for thirty-two in base two decimal128",
    ),
]

# Property [Mixed Type]: $log of mixed numeric types returns decimal128 when either operand is
# decimal128 and double otherwise.
LOG_MIXED_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_int64",
        doc={"value": 100, "base": Int64(10)},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(2.0),
        msg="$log should return two for int32 value and int64 base",
    ),
    ExpressionTestCase(
        "int32_double",
        doc={"value": 100, "base": 10.0},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(2.0),
        msg="$log should return two for int32 value and double base",
    ),
    ExpressionTestCase(
        "int32_decimal",
        doc={"value": 100, "base": Decimal128("10")},
        expression={"$log": ["$value", "$base"]},
        expected=Decimal128("2"),
        msg="$log should return decimal128 two for int32 value and decimal128 base",
    ),
    ExpressionTestCase(
        "int64_double",
        doc={"value": Int64(1000), "base": 10.0},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(3.0),
        msg="$log should return three for int64 value and double base",
    ),
    ExpressionTestCase(
        "int64_decimal",
        doc={"value": Int64(1000), "base": Decimal128("10")},
        expression={"$log": ["$value", "$base"]},
        expected=Decimal128("3.000000000000000000000000000000000"),
        msg="$log should return full-precision decimal128 three for int64 and decimal128 base",
    ),
    ExpressionTestCase(
        "double_decimal",
        doc={"value": 100.0, "base": Decimal128("10")},
        expression={"$log": ["$value", "$base"]},
        expected=Decimal128("2"),
        msg="$log should return decimal128 two for double value and decimal128 base",
    ),
]

# Property [Powers Of Base]: $log of an exact power of the base returns the integer exponent.
LOG_POWER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "base10_ten_thousand",
        doc={"value": 10_000, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(4.0),
        msg="$log should return four for ten thousand in base ten",
    ),
    ExpressionTestCase(
        "base10_million",
        doc={"value": 1_000_000, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(6.0),
        msg="$log should return six for one million in base ten",
    ),
    ExpressionTestCase(
        "base2_64",
        doc={"value": 64, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(6.0),
        msg="$log should return six for sixty-four in base two",
    ),
    ExpressionTestCase(
        "base2_128",
        doc={"value": 128, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(7.0),
        msg="$log should return seven for one hundred twenty-eight in base two",
    ),
    ExpressionTestCase(
        "base2_256",
        doc={"value": 256, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(8.0),
        msg="$log should return eight for two hundred fifty-six in base two",
    ),
    ExpressionTestCase(
        "base5_125",
        doc={"value": 125, "base": 5},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(3.0),
        msg="$log should return three for one hundred twenty-five in base five",
    ),
    ExpressionTestCase(
        "base5_625",
        doc={"value": 625, "base": 5},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(4.0),
        msg="$log should return four for six hundred twenty-five in base five",
    ),
    ExpressionTestCase(
        "base3_27",
        doc={"value": 27, "base": 3},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(3.0),
        msg="$log should return three for twenty-seven in base three",
    ),
    ExpressionTestCase(
        "base3_81",
        doc={"value": 81, "base": 3},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(4.0),
        msg="$log should return four for eighty-one in base three",
    ),
]

# Property [Fractional Result]: $log of a non-power value returns the correct non-integer result.
LOG_FRACTIONAL_RESULT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "base10_50",
        doc={"value": 50, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(1.6989700043360185),
        msg="$log should return the base ten log of fifty",
    ),
    ExpressionTestCase(
        "base10_5",
        doc={"value": 5, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(0.6989700043360187),
        msg="$log should return the base ten log of five",
    ),
    ExpressionTestCase(
        "base2_3",
        doc={"value": 3, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(1.5849625007211563),
        msg="$log should return the base two log of three",
    ),
    ExpressionTestCase(
        "base2_10",
        doc={"value": 10, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(3.3219280948873626),
        msg="$log should return the base two log of ten",
    ),
    ExpressionTestCase(
        "base3_100",
        doc={"value": 100, "base": 3},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(4.19180654857877),
        msg="$log should return the base three log of one hundred",
    ),
    ExpressionTestCase(
        "base10_e",
        doc={"value": math.e, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(0.43429448190325176),
        msg="$log should return the base ten log of e",
    ),
    ExpressionTestCase(
        "base10_pi",
        doc={"value": math.pi, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(0.4971498726941338),
        msg="$log should return the base ten log of pi",
    ),
    ExpressionTestCase(
        "base2_e",
        doc={"value": math.e, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(1.4426950408889634),
        msg="$log should return the base two log of e",
    ),
    ExpressionTestCase(
        "base2_pi",
        doc={"value": math.pi, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(1.651496129472319),
        msg="$log should return the base two log of pi",
    ),
    ExpressionTestCase(
        "base_e_e",
        doc={"value": math.e, "base": math.e},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(1.0),
        msg="$log should return one for e in base e",
    ),
    ExpressionTestCase(
        "base_e_e_squared",
        doc={"value": math.e**2, "base": math.e},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(2.0),
        msg="$log should return two for e squared in base e",
    ),
    ExpressionTestCase(
        "base2_hundred",
        doc={"value": 100, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(6.643856189774725),
        msg="$log should return the base two log of one hundred",
    ),
    ExpressionTestCase(
        "base5_hundred",
        doc={"value": 100, "base": 5},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(2.8613531161467867),
        msg="$log should return the base five log of one hundred",
    ),
    ExpressionTestCase(
        "base2_thousand",
        doc={"value": 1000, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(9.965784284662087),
        msg="$log should return the base two log of one thousand",
    ),
]

# Property [Fractional Value]: $log of a value between zero and one returns a negative result.
LOG_FRACTIONAL_VALUE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "base10_tenth",
        doc={"value": 0.1, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-1.0),
        msg="$log should return negative one for one tenth in base ten",
    ),
    ExpressionTestCase(
        "base10_hundredth",
        doc={"value": 0.01, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-2.0),
        msg="$log should return negative two for one hundredth in base ten",
    ),
    ExpressionTestCase(
        "base2_half",
        doc={"value": 0.5, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-1.0),
        msg="$log should return negative one for one half in base two",
    ),
    ExpressionTestCase(
        "base2_quarter",
        doc={"value": 0.25, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-2.0),
        msg="$log should return negative two for one quarter in base two",
    ),
    ExpressionTestCase(
        "base2_eighth",
        doc={"value": 0.125, "base": 2},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-3.0),
        msg="$log should return negative three for one eighth in base two",
    ),
    ExpressionTestCase(
        "base10_billionth",
        doc={"value": 0.000000001, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-9.0),
        msg="$log should return negative nine for one billionth in base ten",
    ),
    ExpressionTestCase(
        "base10_five_billionth",
        doc={"value": 0.000000005, "base": 10},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-8.301029995663981),
        msg="$log should return the base ten log of five billionths",
    ),
]

LOG_MAGNITUDE_ALL_TESTS = (
    LOG_IDENTITY_TESTS
    + LOG_BASE_EQUALS_VALUE_TESTS
    + LOG_SAME_TYPE_TESTS
    + LOG_MIXED_TYPE_TESTS
    + LOG_POWER_TESTS
    + LOG_FRACTIONAL_RESULT_TESTS
    + LOG_FRACTIONAL_VALUE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LOG_MAGNITUDE_ALL_TESTS))
def test_log_magnitude(collection, test_case: ExpressionTestCase):
    """Test $log logarithm value cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
