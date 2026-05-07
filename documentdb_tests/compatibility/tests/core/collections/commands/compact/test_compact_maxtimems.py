"""Tests for compact command maxTimeMS behavior."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_HALF,
    DOUBLE_MAX,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_OVERFLOW,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [maxTimeMS Acceptance]: maxTimeMS accepts valid numeric values
# that represent non-negative integers within the supported range.
COMPACT_MAXTIMEMS_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "maxtimems_int32_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": 0},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="maxTimeMS=0 as int32 should be accepted",
    ),
    CommandTestCase(
        "maxtimems_int64_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": INT64_ZERO},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="maxTimeMS=0 as Int64 should be accepted",
    ),
    CommandTestCase(
        "maxtimems_double_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": DOUBLE_ZERO},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="maxTimeMS=0 as double should be accepted",
    ),
    CommandTestCase(
        "maxtimems_double_negative_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": DOUBLE_NEGATIVE_ZERO},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="maxTimeMS=-0.0 should be accepted",
    ),
    CommandTestCase(
        "maxtimems_decimal128_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": DECIMAL128_ZERO},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="maxTimeMS=0 as Decimal128 should be accepted",
    ),
    CommandTestCase(
        "maxtimems_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": INT32_MAX},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="maxTimeMS at int32 max as int32 should be accepted",
    ),
    CommandTestCase(
        "maxtimems_int64_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": Int64(INT32_MAX)},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="maxTimeMS at int32 max as Int64 should be accepted",
    ),
    CommandTestCase(
        "maxtimems_double_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": float(INT32_MAX)},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="maxTimeMS at int32 max as double should be accepted",
    ),
    CommandTestCase(
        "maxtimems_decimal128_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "maxTimeMS": Decimal128(str(INT32_MAX)),
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="maxTimeMS at int32 max as Decimal128 should be accepted",
    ),
    CommandTestCase(
        "maxtimems_decimal128_negative_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "maxTimeMS": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="maxTimeMS=Decimal128(-0) should be accepted",
    ),
]

# Property [maxTimeMS Validation Errors]: out-of-range integer values
# produce a bad value error; non-integral or non-representable numeric
# values produce a failed-to-parse error.
COMPACT_MAXTIMEMS_VALIDATION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "maxtimems_int32_max_plus_1",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": INT32_OVERFLOW},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS just above int32 max should be rejected as out of range",
    ),
    CommandTestCase(
        "maxtimems_int64_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": INT64_MAX},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS at Int64 MAX should be rejected as out of range",
    ),
    CommandTestCase(
        "maxtimems_int64_min",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": INT64_MIN},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS at Int64 MIN should be rejected as out of range",
    ),
    CommandTestCase(
        "maxtimems_negative_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": -1},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS=-1 as int32 should be rejected",
    ),
    CommandTestCase(
        "maxtimems_int64_negative_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": Int64(-1)},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS=-1 as Int64 should be rejected",
    ),
    CommandTestCase(
        "maxtimems_double_negative_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": -1.0},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS=-1.0 as double should be rejected",
    ),
    CommandTestCase(
        "maxtimems_decimal128_above_range",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "maxTimeMS": Decimal128(str(INT32_OVERFLOW)),
        },
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS Decimal128 just above int32 max should be rejected",
    ),
    CommandTestCase(
        "maxtimems_decimal128_negative",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "maxTimeMS": Decimal128("-1"),
        },
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS Decimal128 negative should be rejected as out of range",
    ),
    CommandTestCase(
        "maxtimems_fractional_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": DOUBLE_HALF},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS fractional double should be rejected as non-integral",
    ),
    CommandTestCase(
        "maxtimems_double_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": FLOAT_NAN},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS double NaN should be rejected as non-integral",
    ),
    CommandTestCase(
        "maxtimems_double_subnormal",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": DOUBLE_MIN_SUBNORMAL},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS subnormal double should be rejected as non-integral",
    ),
    CommandTestCase(
        "maxtimems_double_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": FLOAT_INFINITY},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS double Infinity should be rejected as non-representable",
    ),
    CommandTestCase(
        "maxtimems_double_negative_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "maxTimeMS": FLOAT_NEGATIVE_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS double -Infinity should be rejected as non-representable",
    ),
    CommandTestCase(
        "maxtimems_double_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": DOUBLE_MAX},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS DBL_MAX should be rejected as non-representable",
    ),
    CommandTestCase(
        "maxtimems_decimal128_fractional_half",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": DECIMAL128_HALF},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS Decimal128 fractional should be rejected as non-representable",
    ),
    CommandTestCase(
        "maxtimems_decimal128_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": DECIMAL128_NAN},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS Decimal128 NaN should be rejected as non-representable",
    ),
    CommandTestCase(
        "maxtimems_decimal128_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "maxTimeMS": DECIMAL128_INFINITY},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS Decimal128 Infinity should be rejected as non-representable",
    ),
    CommandTestCase(
        "maxtimems_decimal128_large_exponent",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "maxTimeMS": DECIMAL128_LARGE_EXPONENT,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS Decimal128 large exponent should be rejected as non-representable",
    ),
    CommandTestCase(
        "maxtimems_decimal128_negative_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "maxTimeMS": DECIMAL128_NEGATIVE_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS Decimal128 -Infinity should be rejected as non-representable",
    ),
]

COMPACT_MAXTIMEMS_TESTS: list[CommandTestCase] = (
    COMPACT_MAXTIMEMS_ACCEPTANCE_TESTS + COMPACT_MAXTIMEMS_VALIDATION_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMPACT_MAXTIMEMS_TESTS))
def test_compact_maxtimems(database_client, collection, test):
    """Test compact command maxTimeMS acceptance and validation."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
