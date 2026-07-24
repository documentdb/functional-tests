"""Tests for autoCompact freeSpaceTargetMB numeric coercion and the lower bound."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.compatibility.tests.system.administration.commands.autoCompact.utils.autoCompact_common import (  # noqa: E501
    ensure_autocompact_idle,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, OBJECT_IS_BUSY_ERROR
from documentdb_tests.framework.executor import execute_admin_with_retry_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INT64_UNDERFLOW,
    DECIMAL128_JUST_ABOVE_HALF,
    DECIMAL128_JUST_BELOW_HALF,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_HALF,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ONE_AND_HALF,
    DOUBLE_ZERO,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT32_OVERFLOW,
    INT64_MIN,
)

# Property [freeSpaceTargetMB Accepted Values]: a freeSpaceTargetMB whose
# coerced value is >= 1 is accepted across all numeric BSON types and across the
# int32/int64 boundary.
AUTOCOMPACT_FSTMB_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "fstmb_min_one",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": 1},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should accept the minimum freeSpaceTargetMB of 1",
    ),
    CommandTestCase(
        "fstmb_type_double",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": 1.0},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should accept a double freeSpaceTargetMB",
    ),
    CommandTestCase(
        "fstmb_type_long",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": Int64(1)},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should accept a long freeSpaceTargetMB",
    ),
    CommandTestCase(
        "fstmb_type_decimal",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": Decimal128("1")},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should accept a decimal freeSpaceTargetMB",
    ),
    CommandTestCase(
        "fstmb_int32_max",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": INT32_MAX},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should accept int32 max as freeSpaceTargetMB",
    ),
    CommandTestCase(
        "fstmb_above_int32_max",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": Int64(INT32_OVERFLOW)},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should accept a long just above int32 max as freeSpaceTargetMB",
    ),
    CommandTestCase(
        "fstmb_decimal_trailing_zero",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_TRAILING_ZERO},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should accept a trailing-zero decimal freeSpaceTargetMB coercing to 1",
    ),
]

# Property [freeSpaceTargetMB Fractional Coercion]: a fractional
# freeSpaceTargetMB is coerced to an integer before validation: doubles
# truncate toward zero and decimals round half-to-even.
AUTOCOMPACT_FSTMB_FRACTIONAL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "fstmb_double_one_and_half",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DOUBLE_ONE_AND_HALF},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should truncate a double freeSpaceTargetMB toward zero to an accepted 1",
    ),
    CommandTestCase(
        "fstmb_decimal_just_above_half_full_precision",
        command=lambda ctx: {
            "autoCompact": True,
            "freeSpaceTargetMB": DECIMAL128_JUST_ABOVE_HALF,
        },
        expected={"ok": Eq(1.0)},
        msg="autoCompact should round a 34-digit just-above-half decimal up to an accepted 1",
    ),
    CommandTestCase(
        "fstmb_decimal_one_and_half",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_ONE_AND_HALF},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should round a decimal half-value half-to-even up to an accepted 2",
    ),
]

# Property [freeSpaceTargetMB Value Validation - Lower Bound]: a
# freeSpaceTargetMB whose coerced integer value is below 1 produces a bad-value
# error.
AUTOCOMPACT_FSTMB_LOWER_BOUND_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "lower_bound_int_zero",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": 0},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should reject an int freeSpaceTargetMB of 0 as below the lower bound",
    ),
    CommandTestCase(
        "lower_bound_int32_min",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": INT32_MIN},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should reject int32 min freeSpaceTargetMB as below the lower bound",
    ),
    CommandTestCase(
        "lower_bound_int64_min",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": INT64_MIN},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should reject int64 min freeSpaceTargetMB as below the lower bound",
    ),
    CommandTestCase(
        "lower_bound_double_zero",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DOUBLE_ZERO},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should reject a double 0.0 freeSpaceTargetMB as below the lower bound",
    ),
    CommandTestCase(
        "lower_bound_double_negative_zero",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DOUBLE_NEGATIVE_ZERO},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should coerce double -0.0 to 0 and reject it as below the lower bound",
    ),
    CommandTestCase(
        "lower_bound_decimal_zero",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_ZERO},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should reject a decimal 0 freeSpaceTargetMB as below the lower bound",
    ),
    CommandTestCase(
        "lower_bound_decimal_negative_zero",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_NEGATIVE_ZERO},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should coerce decimal -0 to 0 and reject it as below the lower bound",
    ),
    CommandTestCase(
        "lower_bound_double_near_one",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": 0.999999},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should truncate a double just below 1 to 0 and reject it as below bound",
    ),
    CommandTestCase(
        "lower_bound_double_negative_half",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DOUBLE_NEGATIVE_HALF},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should truncate double -0.5 to 0 and reject it as below the lower bound",
    ),
    CommandTestCase(
        "lower_bound_decimal_half",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_HALF},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should round decimal 0.5 half-to-even to 0 and reject it below the bound",
    ),
    CommandTestCase(
        "lower_bound_decimal_negative_half",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_NEGATIVE_HALF},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should round decimal -0.5 half-to-even to 0 and reject it below the bound",
    ),
    CommandTestCase(
        "lower_bound_double_min_subnormal",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DOUBLE_MIN_SUBNORMAL},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should truncate the min subnormal double to 0 and reject it below bound",
    ),
    CommandTestCase(
        "lower_bound_decimal_min_positive",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_MIN_POSITIVE},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should coerce the smallest positive decimal to 0 and reject it below "
        "bound",
    ),
    CommandTestCase(
        "lower_bound_decimal_max_negative",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_MAX_NEGATIVE},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should coerce the smallest negative decimal to 0 and reject it below "
        "bound",
    ),
    CommandTestCase(
        "lower_bound_decimal_just_below_half",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_JUST_BELOW_HALF},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should round a 34-digit just-below-half decimal to 0 and reject it below "
        "bound",
    ),
    CommandTestCase(
        "lower_bound_decimal_int64_underflow",
        command=lambda ctx: {
            "autoCompact": True,
            "freeSpaceTargetMB": DECIMAL128_INT64_UNDERFLOW,
        },
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should saturate a below-int64-min decimal to int64 min and reject it "
        "below bound",
    ),
    CommandTestCase(
        "lower_bound_decimal_min",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_MIN},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should saturate a far-negative decimal to int64 min and reject it below "
        "bound",
    ),
    CommandTestCase(
        "lower_bound_decimal_min_disable",
        command=lambda ctx: {"autoCompact": False, "freeSpaceTargetMB": DECIMAL128_MIN},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact disable should still enforce the lower bound on a far-negative decimal",
    ),
    CommandTestCase(
        "lower_bound_double_nan",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": FLOAT_NAN},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should coerce double NaN to 0 and reject it as below the lower bound",
    ),
    CommandTestCase(
        "lower_bound_double_negative_infinity",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": FLOAT_NEGATIVE_INFINITY},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should saturate double -Infinity to int64 min and reject it below bound",
    ),
    CommandTestCase(
        "lower_bound_decimal_nan",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_NAN},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should coerce decimal NaN to 0 and reject it as below the lower bound",
    ),
    CommandTestCase(
        "lower_bound_decimal_negative_infinity",
        command=lambda ctx: {
            "autoCompact": True,
            "freeSpaceTargetMB": DECIMAL128_NEGATIVE_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should saturate decimal -Infinity to int64 min and reject it below bound",
    ),
]

AUTOCOMPACT_FSTMB_BOUNDS_TESTS: list[CommandTestCase] = (
    AUTOCOMPACT_FSTMB_ACCEPTED_TESTS
    + AUTOCOMPACT_FSTMB_FRACTIONAL_TESTS
    + AUTOCOMPACT_FSTMB_LOWER_BOUND_TESTS
)


@pytest.mark.no_parallel
@pytest.mark.parametrize("test", pytest_params(AUTOCOMPACT_FSTMB_BOUNDS_TESTS))
def test_autoCompact_fstmb_bounds(database_client, collection, test):
    """Test autoCompact freeSpaceTargetMB coercion and lower-bound enforcement."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    # Ensure autoCompact is idle first: a leftover config from a prior test
    # would otherwise conflict.
    ensure_autocompact_idle(collection)
    # Tolerate the transient busy state while a prior compaction winds down.
    result = execute_admin_with_retry_command(
        collection, test.build_command(ctx), retry_code=OBJECT_IS_BUSY_ERROR
    )
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
