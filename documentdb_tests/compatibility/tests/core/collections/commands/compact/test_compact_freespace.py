"""Tests for compact command freeSpaceTargetMB validation."""

import uuid
from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_HALF,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    INT32_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [freeSpaceTargetMB Acceptance]: freeSpaceTargetMB accepts valid
# numeric values >= 1 across all numeric BSON types.
COMPACT_FREESPACE_TARGET_MB_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "freespace_accept_int32_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": 1},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="freeSpaceTargetMB=1 as int32 should be accepted",
    ),
    CommandTestCase(
        "freespace_accept_int64_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": Int64(1)},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="freeSpaceTargetMB=1 as Int64 should be accepted",
    ),
    CommandTestCase(
        "freespace_accept_double_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": 1.0},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="freeSpaceTargetMB=1.0 as double should be accepted",
    ),
    CommandTestCase(
        "freespace_accept_decimal128_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": Decimal128("1")},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="freeSpaceTargetMB=1 as Decimal128 should be accepted",
    ),
    CommandTestCase(
        "freespace_accept_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": INT32_MAX},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="freeSpaceTargetMB=INT32_MAX should be accepted",
    ),
    CommandTestCase(
        "freespace_accept_double_fractional",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": 1.5},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="freeSpaceTargetMB=1.5 as double should be accepted",
    ),
    CommandTestCase(
        "freespace_accept_decimal128_fractional",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": DECIMAL128_ONE_AND_HALF,
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="freeSpaceTargetMB=Decimal128(1.5) should be accepted",
    ),
]

# Property [freeSpaceTargetMB Type Strictness]: non-numeric BSON types
# for freeSpaceTargetMB produce a type mismatch error; null is accepted
# and treated as omitted.
COMPACT_FREESPACE_TARGET_MB_TYPE_STRICTNESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "freespace_type_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": "20"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="string freeSpaceTargetMB should be rejected as wrong type",
    ),
    CommandTestCase(
        "freespace_type_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="bool freeSpaceTargetMB should be rejected as wrong type",
    ),
    CommandTestCase(
        "freespace_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": [20]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="array freeSpaceTargetMB should be rejected as wrong type",
    ),
    CommandTestCase(
        "freespace_type_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": {"x": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="object freeSpaceTargetMB should be rejected as wrong type",
    ),
    CommandTestCase(
        "freespace_type_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="ObjectId freeSpaceTargetMB should be rejected as wrong type",
    ),
    CommandTestCase(
        "freespace_type_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="datetime freeSpaceTargetMB should be rejected as wrong type",
    ),
    CommandTestCase(
        "freespace_type_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": Timestamp(1, 1),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Timestamp freeSpaceTargetMB should be rejected as wrong type",
    ),
    CommandTestCase(
        "freespace_type_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": Binary(b"\x01"),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Binary subtype 0 freeSpaceTargetMB should be rejected as wrong type",
    ),
    CommandTestCase(
        "freespace_type_binary_uuid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": Binary(uuid.uuid4().bytes, 4),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Binary subtype 4 (UUID) freeSpaceTargetMB should be rejected as binData",
    ),
    CommandTestCase(
        "freespace_type_binary_user_defined",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": Binary(b"\x01", 128),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Binary subtype 128 freeSpaceTargetMB should be rejected as binData",
    ),
    CommandTestCase(
        "freespace_type_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Regex freeSpaceTargetMB should be rejected as wrong type",
    ),
    CommandTestCase(
        "freespace_type_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": Code("x")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Code freeSpaceTargetMB should be rejected as wrong type",
    ),
    CommandTestCase(
        "freespace_type_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": Code("x", {"a": 1}),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="Code with scope freeSpaceTargetMB should be rejected as wrong type",
    ),
    CommandTestCase(
        "freespace_type_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MinKey freeSpaceTargetMB should be rejected as wrong type",
    ),
    CommandTestCase(
        "freespace_type_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MaxKey freeSpaceTargetMB should be rejected as wrong type",
    ),
]

# Property [freeSpaceTargetMB Value Validation]: numeric values below the
# minimum produce a bad value error.
COMPACT_FREESPACE_TARGET_MB_VALUE_VALIDATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "freespace_value_int32_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": 0},
        error_code=BAD_VALUE_ERROR,
        msg="freeSpaceTargetMB=0 as int32 should be rejected",
    ),
    CommandTestCase(
        "freespace_value_int64_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": INT64_ZERO},
        error_code=BAD_VALUE_ERROR,
        msg="freeSpaceTargetMB=0 as Int64 should be rejected",
    ),
    CommandTestCase(
        "freespace_value_double_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": DOUBLE_ZERO},
        error_code=BAD_VALUE_ERROR,
        msg="freeSpaceTargetMB=0.0 should be rejected",
    ),
    CommandTestCase(
        "freespace_value_double_negative_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": DOUBLE_NEGATIVE_ZERO,
        },
        error_code=BAD_VALUE_ERROR,
        msg="freeSpaceTargetMB=-0.0 should be rejected",
    ),
    CommandTestCase(
        "freespace_value_decimal128_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": DECIMAL128_ZERO,
        },
        error_code=BAD_VALUE_ERROR,
        msg="freeSpaceTargetMB=Decimal128(0) should be rejected",
    ),
    CommandTestCase(
        "freespace_value_decimal128_negative_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": DECIMAL128_NEGATIVE_ZERO,
        },
        error_code=BAD_VALUE_ERROR,
        msg="freeSpaceTargetMB=Decimal128(-0) should be rejected",
    ),
    CommandTestCase(
        "freespace_value_negative_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": -1},
        error_code=BAD_VALUE_ERROR,
        msg="freeSpaceTargetMB=-1 should be rejected",
    ),
    CommandTestCase(
        "freespace_value_double_half",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": DOUBLE_HALF,
        },
        error_code=BAD_VALUE_ERROR,
        msg="freeSpaceTargetMB=0.5 should be rejected",
    ),
    CommandTestCase(
        "freespace_value_decimal128_half",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "freeSpaceTargetMB": DECIMAL128_HALF,
        },
        error_code=BAD_VALUE_ERROR,
        msg="freeSpaceTargetMB=Decimal128(0.5) should be rejected",
    ),
    CommandTestCase(
        "freespace_value_int64_min",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": INT64_MIN},
        error_code=BAD_VALUE_ERROR,
        msg="freeSpaceTargetMB=Int64 MIN should be rejected",
    ),
]

COMPACT_FREESPACE_TESTS: list[CommandTestCase] = (
    COMPACT_FREESPACE_TARGET_MB_ACCEPTANCE_TESTS
    + COMPACT_FREESPACE_TARGET_MB_TYPE_STRICTNESS_TESTS
    + COMPACT_FREESPACE_TARGET_MB_VALUE_VALIDATION_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMPACT_FREESPACE_TESTS))
def test_compact_freespace(database_client, collection, test):
    """Test compact command freeSpaceTargetMB type and value validation."""
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
