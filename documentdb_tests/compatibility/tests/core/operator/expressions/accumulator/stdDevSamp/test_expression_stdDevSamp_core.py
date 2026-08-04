from dataclasses import dataclass
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import (
    DOUBLE_NEGATIVE_ZERO,
)


@dataclass(frozen=True)
class StdDevSampTest(BaseTestCase):
    values: Any = None


STDDEVSAMP_CORE_TESTS: list[StdDevSampTest] = [
    # same type operations
    StdDevSampTest(
        "core_numeric_int32",
        values=[1, 2, 3, 4],
        expected=pytest.approx(1.2909944487358056),
        msg="Should compute sample std dev of int32 values",
    ),
    StdDevSampTest(
        "core_numeric_int64",
        values=[Int64(1), Int64(3), Int64(2), Int64(4)],
        expected=pytest.approx(1.2909944487358056),
        msg="Should compute sample std dev of int64 values",
    ),
    StdDevSampTest(
        "core_numeric_double",
        values=[1.0, 2.0, 4.0, 3.0],
        expected=pytest.approx(1.2909944487358056),
        msg="Should compute sample std dev of double values",
    ),
    StdDevSampTest(
        "core_numeric_decimal128",
        values=[Decimal128("1"), Decimal128("2"), Decimal128("3"), Decimal128("4")],
        expected=pytest.approx(1.2909944487358056),
        msg="Should compute sample std dev of decimal128 values",
    ),
    # mix type operation
    StdDevSampTest(
        "core_numeric_mix",
        values=[Decimal128("1"), Int64(2), 3, 4.0],
        expected=pytest.approx(1.2909944487358056),
        msg="Should compute sample std dev of mix numerical values",
    ),
    # fractional
    StdDevSampTest(
        "core_fractional_double",
        values=[1.5, 2.5],
        expected=pytest.approx(0.7071067811865476),
        msg="Should compute sample std dev of fractional double values",
    ),
    StdDevSampTest(
        "core_fractional_decimal",
        values=[Decimal128("1.5"), Decimal128("2.5")],
        expected=pytest.approx(0.7071067811865476),
        msg="Should compute sample std dev of fractional decimal values",
    ),
    # negative operation
    StdDevSampTest(
        "core_numeric_negative",
        values=[-1, -2, -3, -4],
        expected=pytest.approx(1.2909944487358056),
        msg="Should compute sample std dev of negative values",
    ),
    StdDevSampTest(
        "core_numeric_mixed_signs",
        values=[-3, 3, 9],
        expected=pytest.approx(6.0),
        msg="Should compute sample std dev of both positive and negative values",
    ),
    StdDevSampTest(
        "core_negative_zero",
        values=[DOUBLE_NEGATIVE_ZERO, DOUBLE_NEGATIVE_ZERO],
        expected=0.0,
        msg="Should compute sample std dev treating negative zero as zero",
    ),
    # large N
    StdDevSampTest(
        "core_large_n",
        values=list(range(1000)),
        expected=pytest.approx(288.8194360957494),
        msg="Should compute sample std dev of all 1000 values",
    ),
    # dec_high_precision_not_preserved
    StdDevSampTest(
        "core_high_precision",
        values=[Decimal128("1.000000000000000000000000000000001"), Decimal128("1.0")],
        expected=pytest.approx(0.0),
        msg="Should match preservation behavior for high-precision Decimal128 inputs",
    ),
    # N<2 -> null rule
    StdDevSampTest(
        "core_single_value",
        values=[5],
        expected=None,
        msg="Should return null when single value",
    ),
    StdDevSampTest(
        "core_no_value",
        values=[],
        expected=None,
        msg="Should return null when no values",
    ),
    StdDevSampTest(
        "core_scalar_value",
        values=42,
        expected=None,
        msg="Should return null when scalar value",
    ),
    # zero variance
    StdDevSampTest(
        "core_zero_variance",
        values=[5, 5, 5],
        expected=0.0,
        msg="Should return 0.0 when there's no variance",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STDDEVSAMP_CORE_TESTS))
def test_stdDevSamp_core_from_list(collection, test_case: StdDevSampTest):
    """Test $stdDevSamp expression core properties from a literal argument list."""

    result = execute_expression(collection, {"$stdDevSamp": test_case.values})

    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


@pytest.mark.parametrize("test_case", pytest_params(STDDEVSAMP_CORE_TESTS))
def test_stdDevSamp_core_from_field(collection, test_case: StdDevSampTest):
    """Test $stdDevSamp expression core properties from an inserted array field."""
    result = execute_expression_with_insert(
        collection, {"$stdDevSamp": "$values"}, {"values": test_case.values}
    )

    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
