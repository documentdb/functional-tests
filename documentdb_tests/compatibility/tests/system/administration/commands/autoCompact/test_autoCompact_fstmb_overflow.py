"""Tests for the autoCompact freeSpaceTargetMB MB-to-bytes overflow boundary."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.compatibility.tests.system.administration.commands.autoCompact.utils.autoCompact_common import (  # noqa: E501
    ensure_autocompact_idle,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_MAX,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    FLOAT_INFINITY,
    INT64_MAX,
)

# freeSpaceTargetMB is converted to bytes as a signed int64 (value * 2^20), so
# the largest value whose byte product still fits is INT64_MAX // 2^20 and the
# smallest value that overflows to a negative signed int64 is one past it.
_MB_IN_BYTES = 1 << 20
_FSTMB_BYTE_OVERFLOW = INT64_MAX // _MB_IN_BYTES + 1

# Property [freeSpaceTargetMB Enable/Disable Path Asymmetry]: the MB-to-bytes
# overflow check runs only on the enable path, so a freeSpaceTargetMB whose byte
# product overflows signed int64 is accepted when disabling.
AUTOCOMPACT_FSTMB_PATH_ASYMMETRY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "path_disable_overflow",
        command=lambda ctx: {
            "autoCompact": False,
            "freeSpaceTargetMB": Int64(_FSTMB_BYTE_OVERFLOW),
        },
        expected={"ok": Eq(1.0)},
        msg="autoCompact disable should accept a freeSpaceTargetMB whose byte product overflows",
    ),
]

# Property [freeSpaceTargetMB Value Validation - Byte-Level Minimum]: a
# freeSpaceTargetMB that passes the lower bound but whose byte conversion wraps
# back to zero, below the byte minimum, is still rejected. Unlike the overflow
# cases the wrapped product is non-negative, so an implementation guarding only
# against a negative wrap would wrongly accept it; this region needs separate
# coverage.
AUTOCOMPACT_FSTMB_BYTE_MINIMUM_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "byte_minimum_double_max_safe_integer",
        command=lambda ctx: {
            "autoCompact": True,
            "freeSpaceTargetMB": float(DOUBLE_MAX_SAFE_INTEGER),
        },
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should reject a freeSpaceTargetMB whose byte product wraps to zero",
    ),
]

# Property [freeSpaceTargetMB Overflow Boundary]: the largest freeSpaceTargetMB
# whose byte product still fits in signed int64 is accepted on the enable path.
AUTOCOMPACT_FSTMB_OVERFLOW_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "overflow_accepted_boundary",
        command=lambda ctx: {
            "autoCompact": True,
            "freeSpaceTargetMB": Int64(_FSTMB_BYTE_OVERFLOW - 1),
        },
        expected={"ok": Eq(1.0)},
        msg="autoCompact should accept the largest freeSpaceTargetMB whose byte product stays "
        "positive",
    ),
]

# Property [freeSpaceTargetMB Value Validation - Overflow]: on the enable path,
# a freeSpaceTargetMB whose MB-to-bytes product wraps to a negative signed int64
# produces a bad-value error.
AUTOCOMPACT_FSTMB_OVERFLOW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "overflow_boundary_plus_one",
        command=lambda ctx: {
            "autoCompact": True,
            "freeSpaceTargetMB": Int64(_FSTMB_BYTE_OVERFLOW),
        },
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should reject the smallest freeSpaceTargetMB whose byte product wraps "
        "negative",
    ),
    CommandTestCase(
        "overflow_int64_max",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": INT64_MAX},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should reject int64 max freeSpaceTargetMB whose byte product overflows",
    ),
    CommandTestCase(
        "overflow_double_from_int64_max",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DOUBLE_FROM_INT64_MAX},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should reject the int64-max-as-double freeSpaceTargetMB in the overflow "
        "region",
    ),
    CommandTestCase(
        "overflow_double_max",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DOUBLE_MAX},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should reject the max double freeSpaceTargetMB in the overflow region",
    ),
    CommandTestCase(
        "overflow_double_infinity",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": FLOAT_INFINITY},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should reject double +Infinity freeSpaceTargetMB in the overflow region",
    ),
    CommandTestCase(
        "overflow_decimal_max",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_MAX},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should reject the max decimal freeSpaceTargetMB in the overflow region",
    ),
    CommandTestCase(
        "overflow_decimal_int64_overflow",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_INT64_OVERFLOW},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should absorb an above-int64-max decimal freeSpaceTargetMB into the "
        "overflow path",
    ),
    CommandTestCase(
        "overflow_decimal_infinity",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": DECIMAL128_INFINITY},
        error_code=BAD_VALUE_ERROR,
        msg="autoCompact should reject decimal Infinity freeSpaceTargetMB in the overflow region",
    ),
]

AUTOCOMPACT_FSTMB_OVERFLOW_BOUNDARY_TESTS: list[CommandTestCase] = (
    AUTOCOMPACT_FSTMB_PATH_ASYMMETRY_TESTS
    + AUTOCOMPACT_FSTMB_BYTE_MINIMUM_TESTS
    + AUTOCOMPACT_FSTMB_OVERFLOW_ACCEPTED_TESTS
    + AUTOCOMPACT_FSTMB_OVERFLOW_TESTS
)


@pytest.mark.no_parallel
@pytest.mark.parametrize("test", pytest_params(AUTOCOMPACT_FSTMB_OVERFLOW_BOUNDARY_TESTS))
def test_autoCompact_fstmb_overflow(database_client, collection, test):
    """Test autoCompact freeSpaceTargetMB MB-to-bytes overflow boundary behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    # Ensure autoCompact is idle first: a leftover config from a prior test
    # would otherwise conflict.
    ensure_autocompact_idle(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
