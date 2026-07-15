import math
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
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)


@dataclass(frozen=True)
class ModTest(BaseTestCase):
    """Test case for $mod operator."""

    dividend: Any = None
    divisor: Any = None


MOD_NAN_INFINITY_TESTS: list[ModTest] = [
    ModTest(
        "neg_inf_divisor",
        dividend=10,
        divisor=FLOAT_NEGATIVE_INFINITY,
        expected=10.0,
        msg="Should return dividend when divisor is -infinity",
    ),
    ModTest(
        "decimal_neg_inf_divisor",
        dividend=10,
        divisor=DECIMAL128_NEGATIVE_INFINITY,
        expected=Decimal128("10"),
        msg="Should return dividend when divisor is decimal -infinity",
    ),
    ModTest(
        "nan_dividend",
        dividend=FLOAT_NAN,
        divisor=3,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN when dividend is NaN",
    ),
    ModTest(
        "nan_divisor",
        dividend=10,
        divisor=FLOAT_NAN,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN when divisor is NaN",
    ),
    ModTest(
        "both_nan",
        dividend=FLOAT_NAN,
        divisor=FLOAT_NAN,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN when both are NaN",
    ),
    ModTest(
        "inf_dividend",
        dividend=FLOAT_INFINITY,
        divisor=3,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for infinity mod finite",
    ),
    ModTest(
        "neg_inf_dividend",
        dividend=FLOAT_NEGATIVE_INFINITY,
        divisor=3,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for -infinity mod finite",
    ),
    ModTest(
        "decimal_nan_dividend",
        dividend=DECIMAL128_NAN,
        divisor=3,
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN when dividend is decimal NaN",
    ),
    ModTest(
        "decimal_nan_divisor",
        dividend=10,
        divisor=DECIMAL128_NAN,
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN when divisor is decimal NaN",
    ),
    ModTest(
        "decimal_inf_dividend",
        dividend=DECIMAL128_INFINITY,
        divisor=3,
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN for decimal infinity mod finite",
    ),
    ModTest(
        "inf_mod_inf",
        dividend=FLOAT_INFINITY,
        divisor=FLOAT_INFINITY,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for infinity mod infinity",
    ),
    ModTest(
        "neg_inf_mod_neg_inf",
        dividend=FLOAT_NEGATIVE_INFINITY,
        divisor=FLOAT_NEGATIVE_INFINITY,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for -infinity mod -infinity",
    ),
    ModTest(
        "inf_mod_neg_inf",
        dividend=FLOAT_INFINITY,
        divisor=FLOAT_NEGATIVE_INFINITY,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for infinity mod -infinity",
    ),
    ModTest(
        "neg_inf_mod_inf",
        dividend=FLOAT_NEGATIVE_INFINITY,
        divisor=FLOAT_INFINITY,
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for -infinity mod infinity",
    ),
    ModTest(
        "decimal_inf_mod_inf",
        dividend=DECIMAL128_INFINITY,
        divisor=DECIMAL128_INFINITY,
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN for decimal infinity mod decimal infinity",
    ),
    ModTest(
        "decimal_neg_inf_mod_neg_inf",
        dividend=DECIMAL128_NEGATIVE_INFINITY,
        divisor=DECIMAL128_NEGATIVE_INFINITY,
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN for decimal -infinity mod decimal -infinity",
    ),
    ModTest(
        "decimal_inf_mod_neg_inf",
        dividend=DECIMAL128_INFINITY,
        divisor=DECIMAL128_NEGATIVE_INFINITY,
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN for decimal infinity mod decimal -infinity",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_NAN_INFINITY_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.dividend, test.divisor]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_NAN_INFINITY_TESTS))
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
