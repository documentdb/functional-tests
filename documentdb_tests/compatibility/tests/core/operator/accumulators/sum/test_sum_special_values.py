"""Tests for $sum accumulator: special float values, Decimal128 specials, and precision."""

from __future__ import annotations

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX_COEFFICIENT,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_MAX,
)

# Property [Special Float Values]: NaN propagates through summation and
# dominates all other values; inf + (-inf) produces NaN; inf + inf produces
# inf; inf + finite produces inf; non-numeric values are ignored.
SUM_SPECIAL_FLOAT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "special_float_inf_plus_inf",
        docs=[{"v": FLOAT_INFINITY}, {"v": FLOAT_INFINITY}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=FLOAT_INFINITY,
        msg="$sum should produce inf when summing inf + inf",
    ),
    AccumulatorTestCase(
        "special_float_neg_inf_plus_neg_inf",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should produce -inf when summing -inf + -inf",
    ),
    AccumulatorTestCase(
        "special_float_inf_plus_finite",
        docs=[{"v": FLOAT_INFINITY}, {"v": 42.0}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=FLOAT_INFINITY,
        msg="$sum should produce inf when summing inf + finite",
    ),
    AccumulatorTestCase(
        "special_float_neg_inf_plus_finite",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": 42.0}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should produce -inf when summing -inf + finite",
    ),
    AccumulatorTestCase(
        "special_float_nan_propagates",
        docs=[{"v": FLOAT_NAN}, {"v": 5.0}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should propagate NaN through summation",
    ),
    AccumulatorTestCase(
        "special_float_nan_dominates_inf",
        docs=[{"v": FLOAT_NAN}, {"v": FLOAT_INFINITY}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should produce NaN when NaN is summed with inf",
    ),
    AccumulatorTestCase(
        "special_float_inf_plus_neg_inf",
        docs=[{"v": FLOAT_INFINITY}, {"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should produce NaN for inf + (-inf) indeterminate form",
    ),
    AccumulatorTestCase(
        "special_float_non_numeric_with_nan",
        docs=[{"v": "hello"}, {"v": FLOAT_NAN}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should ignore non-numeric values and preserve NaN",
    ),
]

# Property [Decimal128 Special Values]: Decimal128 NaN propagates through
# summation, Decimal128 Infinity + Decimal128 -Infinity produces Decimal128
# NaN, and Decimal128 Infinity + Decimal128 Infinity produces Decimal128
# Infinity.
SUM_DECIMAL128_SPECIAL_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal128_special_nan_propagates",
        docs=[{"v": DECIMAL128_NAN}, {"v": Decimal128("5")}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=DECIMAL128_NAN,
        msg="$sum should propagate Decimal128 NaN through summation",
    ),
    AccumulatorTestCase(
        "decimal128_special_inf_plus_neg_inf",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DECIMAL128_NEGATIVE_INFINITY}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=DECIMAL128_NAN,
        msg="$sum should produce Decimal128 NaN for Decimal128 Infinity + -Infinity",
    ),
    AccumulatorTestCase(
        "decimal128_special_inf_plus_inf",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": DECIMAL128_INFINITY}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=DECIMAL128_INFINITY,
        msg="$sum should produce Decimal128 Infinity for Decimal128 Infinity + Infinity",
    ),
]

# Property [Precision]: Decimal128 provides exact arithmetic and preserves
# trailing zeros based on the highest-precision operand, while double follows
# IEEE 754 rules with precision loss for large values and correct handling of
# subnormal values.
SUM_PRECISION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "precision_decimal128_exact",
        docs=[{"v": Decimal128("0.1")} for _ in range(100)],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=Decimal128("10.0"),
        msg="$sum should produce exact Decimal128 result for 100 x 0.1",
    ),
    AccumulatorTestCase(
        "precision_decimal128_trailing_zeros",
        docs=[{"v": Decimal128("1.100")}, {"v": Decimal128("2.20")}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=Decimal128("3.300"),
        msg="$sum should preserve trailing zeros based on highest-precision operand",
    ),
    AccumulatorTestCase(
        "precision_double_accumulation",
        docs=[{"v": 0.1} for _ in range(100)],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=10.0,
        msg="$sum should produce 10.0 for 100 x double 0.1 due to accumulation",
    ),
    AccumulatorTestCase(
        "precision_double_loss_large_value",
        docs=[{"v": 1e16}, {"v": 1.0}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=1e16,
        msg="$sum should lose precision for double when adding 1.0 to 1e16",
    ),
    AccumulatorTestCase(
        "precision_int64_max_plus_decimal128_exact",
        docs=[{"v": INT64_MAX}, {"v": Decimal128("1")}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=DECIMAL128_INT64_OVERFLOW,
        msg="$sum should preserve exact value for Int64_max + Decimal128(1)",
    ),
    AccumulatorTestCase(
        "precision_int64_max_plus_double_loses",
        docs=[{"v": INT64_MAX}, {"v": 1.0}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=DOUBLE_FROM_INT64_MAX,
        msg="$sum should lose precision for Int64_max + double(1.0)",
    ),
    AccumulatorTestCase(
        "precision_subnormal_double_addition",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}, {"v": DOUBLE_MIN_SUBNORMAL}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=1e-323,
        msg="$sum should correctly add subnormal double values",
    ),
    AccumulatorTestCase(
        "precision_subnormal_double_negative",
        docs=[{"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}, {"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=-1e-323,
        msg="$sum should correctly add negative subnormal double values",
    ),
    AccumulatorTestCase(
        "precision_subnormal_double_cancellation",
        docs=[{"v": DOUBLE_MIN_SUBNORMAL}, {"v": DOUBLE_MIN_NEGATIVE_SUBNORMAL}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=DOUBLE_ZERO,
        msg="$sum should produce 0.0 when subnormal values cancel",
    ),
    AccumulatorTestCase(
        "precision_decimal128_subnormal",
        docs=[{"v": DECIMAL128_MIN_POSITIVE}, {"v": DECIMAL128_MIN_POSITIVE}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=Decimal128("2E-6176"),
        msg="$sum should correctly add Decimal128 subnormal values",
    ),
    AccumulatorTestCase(
        "precision_decimal128_large_exponent",
        docs=[{"v": DECIMAL128_LARGE_EXPONENT}, {"v": DECIMAL128_LARGE_EXPONENT}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=Decimal128("2.000000000000000000000000000000000E+6144"),
        msg="$sum should correctly add Decimal128 large exponent values",
    ),
    AccumulatorTestCase(
        "precision_decimal128_34_digit_overflow",
        docs=[{"v": DECIMAL128_MAX_COEFFICIENT}, {"v": Decimal128("1")}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=Decimal128("1.000000000000000000000000000000000E+34"),
        msg="$sum should round correctly when Decimal128 34-digit precision overflows",
    ),
]

SUM_SPECIAL_VALUE_TESTS = (
    SUM_SPECIAL_FLOAT_TESTS + SUM_DECIMAL128_SPECIAL_TESTS + SUM_PRECISION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUM_SPECIAL_VALUE_TESTS))
def test_sum_special_values(collection, test_case: AccumulatorTestCase):
    """Test $sum special float values, Decimal128 specials, and precision."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(
        result,
        [{"_id": None, "result": test_case.expected}],
        msg=test_case.msg,
    )
