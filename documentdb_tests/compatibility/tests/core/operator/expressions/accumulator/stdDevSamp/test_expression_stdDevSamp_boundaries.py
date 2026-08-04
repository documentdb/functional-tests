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
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MIN,
    DOUBLE_PRECISION_LOSS,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT32_OVERFLOW,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)


@dataclass(frozen=True)
class StdDevSampTest(BaseTestCase):
    values: Any = None


STDDEVSAMP_BOUNDARIES_TESTS: list[StdDevSampTest] = [
    # boundaries
    StdDevSampTest(
        "bound_int32_max",
        values=[INT32_MAX, INT32_MAX_MINUS_1],
        expected=pytest.approx(0.7071067811865476),
        msg="Should compute sample std dev for values near the int32 maximum",
    ),
    StdDevSampTest(
        "bound_int32_min",
        values=[INT32_MIN, INT32_MIN_PLUS_1],
        expected=pytest.approx(0.7071067811865476),
        msg="Should compute sample std dev for values near the int32 minimum",
    ),
    StdDevSampTest(
        "bound_int64_max",
        values=[INT64_MAX, INT64_MAX_MINUS_1],
        expected=0.0,
        msg="Should return 0.0 when int64 max values are indistinguishable at double precision",
    ),
    StdDevSampTest(
        "bound_int64_min",
        values=[INT64_MIN, INT64_MIN_PLUS_1],
        expected=0.0,
        msg="Should return 0.0 when int64 min values are indistinguishable at double precision",
    ),
    StdDevSampTest(
        "bound_int32_overflow",
        values=[INT32_MAX, INT32_OVERFLOW],
        expected=pytest.approx(0.7071067811865476),
        msg="Should handle value at int32 overflow boundary",
    ),
    StdDevSampTest(
        "bound_double_max",
        values=[DOUBLE_MAX, DOUBLE_MAX - 1],
        expected=0.0,
        msg="Should return 0.0 when values are indistinguishable at double maximum precision",
    ),
    StdDevSampTest(
        "bound_double_near_0",
        values=[DOUBLE_NEAR_MIN, 2e-308, 3e-308],
        expected=0.0,
        msg="Should return 0.0 when near-min doubles are indistinguishable at double precision",
    ),
    StdDevSampTest(
        "bound_double_subnormal",
        values=[DOUBLE_MIN_SUBNORMAL, DOUBLE_NEAR_MIN],
        expected=0.0,
        msg="Should return 0.0 for indistinguishable subnormal doubles at double precision",
    ),
    StdDevSampTest(
        "bound_double_full_range",
        values=[DOUBLE_MIN, DOUBLE_MAX],
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN when double range spread overflows during variance computation",
    ),
    StdDevSampTest(
        "bound_double_precision_loss",
        values=[DOUBLE_MAX_SAFE_INTEGER, DOUBLE_PRECISION_LOSS],
        expected=0.0,
        msg="Should return 0.0 when values are indistinguishable due to double precision loss",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STDDEVSAMP_BOUNDARIES_TESTS))
def test_stdDevSamp_boundaries_from_list(collection, test_case: StdDevSampTest):
    """Test $stdDevSamp expression boundaries from a literal argument list."""

    result = execute_expression(collection, {"$stdDevSamp": test_case.values})

    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


@pytest.mark.parametrize("test_case", pytest_params(STDDEVSAMP_BOUNDARIES_TESTS))
def test_stdDevSamp_boundaries_from_field(collection, test_case: StdDevSampTest):
    """Test $stdDevSamp expression boundaries from an inserted array field."""
    result = execute_expression_with_insert(
        collection, {"$stdDevSamp": "$values"}, {"values": test_case.values}
    )

    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
