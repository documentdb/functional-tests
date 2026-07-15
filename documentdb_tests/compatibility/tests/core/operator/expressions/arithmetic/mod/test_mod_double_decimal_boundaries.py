from dataclasses import dataclass
from typing import Any

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import (
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_SMALL_EXPONENT,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
)


@dataclass(frozen=True)
class ModTest(BaseTestCase):
    """Test case for $mod operator."""

    dividend: Any = None
    divisor: Any = None


MOD_DOUBLE_DECIMAL_BOUNDARY_TESTS: list[ModTest] = [
    ModTest(
        "negative_zero_double_dividend",
        dividend=DOUBLE_NEGATIVE_ZERO,
        divisor=3,
        expected=DOUBLE_NEGATIVE_ZERO,
        msg="Should preserve sign for negative zero double dividend",
    ),
    ModTest(
        "negative_zero_decimal_dividend",
        dividend=DECIMAL128_NEGATIVE_ZERO,
        divisor=Decimal128("3"),
        expected=DECIMAL128_NEGATIVE_ZERO,
        msg="Should preserve sign for negative zero decimal128 dividend",
    ),
    ModTest(
        "inf_divisor",
        dividend=10,
        divisor=FLOAT_INFINITY,
        expected=10.0,
        msg="Should return dividend when divisor is infinity",
    ),
    ModTest(
        "huge_modulo",
        dividend=DOUBLE_NEAR_MAX,
        divisor=7,
        expected=3.0,
        msg="Should handle near-max double as dividend",
    ),
    ModTest(
        "min_subnormal_modulo",
        dividend=DOUBLE_MIN_SUBNORMAL,
        divisor=3,
        expected=DOUBLE_MIN_SUBNORMAL,
        msg="Should handle min subnormal double as dividend",
    ),
    ModTest(
        "decimal_precision",
        dividend=Decimal128("10.5"),
        divisor=Decimal128("3.2"),
        expected=Decimal128("0.9"),
        msg="Should preserve decimal128 precision",
    ),
    ModTest(
        "decimal_max_dividend",
        dividend=DECIMAL128_MAX,
        divisor=Decimal128("3"),
        expected=Decimal128("0"),
        msg="Should handle Decimal128 max value as dividend",
    ),
    ModTest(
        "decimal_min_dividend",
        dividend=DECIMAL128_MIN,
        divisor=Decimal128("3"),
        expected=Decimal128("-0"),
        msg="Should handle Decimal128 min value as dividend",
    ),
    ModTest(
        "decimal_large_exponent_dividend",
        dividend=DECIMAL128_LARGE_EXPONENT,
        divisor=Decimal128("3"),
        expected=Decimal128("1"),
        msg="Should handle Decimal128 large exponent as dividend",
    ),
    ModTest(
        "decimal_small_exponent_dividend",
        dividend=DECIMAL128_SMALL_EXPONENT,
        divisor=Decimal128("3"),
        expected=DECIMAL128_SMALL_EXPONENT,
        msg="Should handle Decimal128 small exponent as dividend",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_DOUBLE_DECIMAL_BOUNDARY_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.dividend, test.divisor]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_DOUBLE_DECIMAL_BOUNDARY_TESTS))
def test_mod_insert(collection, test):
    """Test $mod from documents"""
    result = execute_expression_with_insert(
        collection,
        {"$mod": ["$dividend", "$divisor"]},
        {"dividend": test.dividend, "divisor": test.divisor},
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
