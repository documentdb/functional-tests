import math
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
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
)


@dataclass(frozen=True)
class StdDevSampTest(BaseTestCase):
    values: Any = None


STDDEVSAMP_INFINITY_TESTS: list[StdDevSampTest] = [
    StdDevSampTest(
        "inf_scalar",
        values=FLOAT_INFINITY,
        expected=None,
        msg="Should return None for a double infinity scalar",
    ),
    StdDevSampTest(
        "negative_inf_scalar",
        values=FLOAT_NEGATIVE_INFINITY,
        expected=None,
        msg="Should return None for a negative double infinity scalar",
    ),
    StdDevSampTest(
        "decimal_inf_scalar",
        values=DECIMAL128_INFINITY,
        expected=None,
        msg="Should return None for a decimal infinity scalar",
    ),
    StdDevSampTest(
        "negative_decimal_inf_scalar",
        values=DECIMAL128_NEGATIVE_INFINITY,
        expected=None,
        msg="Should return None for a negative decimal infinity scalar",
    ),
    StdDevSampTest(
        "inf_single_array",
        values=[FLOAT_INFINITY],
        expected=None,
        msg="Should return None for a double infinity single element array",
    ),
    StdDevSampTest(
        "negative_inf_single_array",
        values=[FLOAT_NEGATIVE_INFINITY],
        expected=None,
        msg="Should return None for a negative double infinity single element array",
    ),
    StdDevSampTest(
        "decimal_inf_single_array",
        values=[DECIMAL128_INFINITY],
        expected=None,
        msg="Should return None for a decimal infinity single element array",
    ),
    StdDevSampTest(
        "negative_decimal_inf_single_array",
        values=[DECIMAL128_NEGATIVE_INFINITY],
        expected=None,
        msg="Should return None for a negative decimal infinity single element array",
    ),
    StdDevSampTest(
        "inf_with_finite",
        values=[1, 2, 3, FLOAT_INFINITY],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN if a double infinity is present",
    ),
    StdDevSampTest(
        "negative_inf_with_finite",
        values=[1, 2, 3, FLOAT_NEGATIVE_INFINITY],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN if a negative double infinity is present",
    ),
    StdDevSampTest(
        "decimal_inf_with_finite",
        values=[1, 2, 3, DECIMAL128_INFINITY],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN if a decimal infinity is present",
    ),
    StdDevSampTest(
        "negative_decimal_inf_with_finite",
        values=[1, 2, 3, DECIMAL128_NEGATIVE_INFINITY],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN if a negative decimal infinity is present",
    ),
    StdDevSampTest(
        "inf_same_sign_pair",
        values=[FLOAT_INFINITY, FLOAT_INFINITY],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for a double infinity pair of same signs",
    ),
    StdDevSampTest(
        "inf_opp_sign_pair",
        values=[FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for a double infinity pair of opposite signs",
    ),
    StdDevSampTest(
        "decimal_inf_same_sign_pair",
        values=[DECIMAL128_INFINITY, DECIMAL128_INFINITY],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for a decimal infinity pair of same signs",
    ),
    StdDevSampTest(
        "decimal_inf_opp_sign_pair",
        values=[DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for a decimal infinity pair of opposite signs",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STDDEVSAMP_INFINITY_TESTS))
def test_stdDevSamp_infinity_from_list(collection, test_case: StdDevSampTest):
    """Test $stdDevSamp expression infinity properties from a literal argument list."""

    result = execute_expression(collection, {"$stdDevSamp": test_case.values})

    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


@pytest.mark.parametrize("test_case", pytest_params(STDDEVSAMP_INFINITY_TESTS))
def test_stdDevSamp_infinity_from_field(collection, test_case: StdDevSampTest):
    """Test $stdDevSamp expression infinity properties from an inserted array field."""
    result = execute_expression_with_insert(
        collection, {"$stdDevSamp": "$values"}, {"values": test_case.values}
    )

    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
