from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ModTest(BaseTestCase):
    """Test case for $mod operator."""

    dividend: Any = None
    divisor: Any = None


MOD_BASIC_SIGN_TESTS: list[ModTest] = [
    ModTest(
        "remainder_two",
        dividend=10,
        divisor=4,
        expected=2,
        msg="Should return correct remainder",
    ),
    ModTest(
        "smaller_dividend",
        dividend=5,
        divisor=10,
        expected=5,
        msg="Should return dividend when smaller than divisor",
    ),
    ModTest(
        "negative_dividend",
        dividend=-10,
        divisor=3,
        expected=-1,
        msg="Should preserve sign of negative dividend",
    ),
    ModTest(
        "negative_divisor",
        dividend=10,
        divisor=-3,
        expected=1,
        msg="Should return positive remainder for negative divisor",
    ),
    ModTest(
        "both_negative",
        dividend=-10,
        divisor=-3,
        expected=-1,
        msg="Should preserve dividend sign when both negative",
    ),
    ModTest(
        "zero_dividend",
        dividend=0,
        divisor=5,
        expected=0,
        msg="Should return 0 when dividend is zero",
    ),
    ModTest(
        "small_fractional",
        dividend=5.5,
        divisor=2.5,
        expected=pytest.approx(0.5),
        msg="Should handle small fractional operands",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_BASIC_SIGN_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.dividend, test.divisor]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_BASIC_SIGN_TESTS))
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
