"""Tests for compact command freeSpaceTargetMB overflow behavior.

Values where freeSpaceTargetMB * 1048576 overflows int64 cause a server crash
on the reference engine due to an unhandled error from the storage layer.
These tests document the expected behavior: the server should either accept
the value gracefully or return an error, but must not crash.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DOUBLE_MAX,
    FLOAT_INFINITY,
    INT64_MAX,
    INT64_ZERO,
)

_SKIP_REASON = "Server crashes when freeSpaceTargetMB * 1048576 overflows int64"

# Property [freeSpaceTargetMB Overflow]: values where the MB-to-bytes
# conversion overflows int64 are accepted and the command succeeds.
COMPACT_FREESPACE_OVERFLOW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "freespace_overflow_int64_boundary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": Int64(8796093022208),
        },
        expected={"bytesFreed": INT64_ZERO, "ok": 1.0},
        msg="freeSpaceTargetMB at overflow boundary should not crash the server",
        marks=(pytest.mark.engine_xcrash(engine="mongodb", reason=_SKIP_REASON),),
    ),
    CommandTestCase(
        "freespace_overflow_int64_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": INT64_MAX},
        expected={"bytesFreed": INT64_ZERO, "ok": 1.0},
        msg="freeSpaceTargetMB=INT64_MAX should not crash the server",
        marks=(pytest.mark.engine_xcrash(engine="mongodb", reason=_SKIP_REASON),),
    ),
    CommandTestCase(
        "freespace_overflow_double_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": FLOAT_INFINITY},
        expected={"bytesFreed": INT64_ZERO, "ok": 1.0},
        msg="freeSpaceTargetMB=Infinity should not crash the server",
        marks=(pytest.mark.engine_xcrash(engine="mongodb", reason=_SKIP_REASON),),
    ),
    CommandTestCase(
        "freespace_overflow_double_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": DOUBLE_MAX},
        expected={"bytesFreed": INT64_ZERO, "ok": 1.0},
        msg="freeSpaceTargetMB=DBL_MAX should not crash the server",
        marks=(pytest.mark.engine_xcrash(engine="mongodb", reason=_SKIP_REASON),),
    ),
    CommandTestCase(
        "freespace_overflow_decimal128_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": DECIMAL128_INFINITY,
        },
        expected={"bytesFreed": INT64_ZERO, "ok": 1.0},
        msg="freeSpaceTargetMB=Decimal128(Infinity) should not crash the server",
        marks=(pytest.mark.engine_xcrash(engine="mongodb", reason=_SKIP_REASON),),
    ),
    CommandTestCase(
        "freespace_overflow_decimal128_large_exponent",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": Decimal128("1E+100"),
        },
        expected={"bytesFreed": INT64_ZERO, "ok": 1.0},
        msg="freeSpaceTargetMB=Decimal128(1E+100) should not crash the server",
        marks=(pytest.mark.engine_xcrash(engine="mongodb", reason=_SKIP_REASON),),
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMPACT_FREESPACE_OVERFLOW_TESTS))
def test_compact_freespace_overflow(database_client, collection, test):
    """Test compact command freeSpaceTargetMB overflow handling."""
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
