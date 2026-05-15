"""Tests for renameCollection maxTimeMS parameter validation."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.renameCollection.utils.renameCollection_common import (  # noqa: E501
    cross_db_cleanup_ns,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_OVERFLOW,
)

# Property [maxTimeMS Success]: maxTimeMS accepts numeric values that
# represent a non-negative integer within int32 range.
RENAME_MAX_TIME_MS_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_time_ms_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": 0,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS=0 should succeed",
    ),
    CommandTestCase(
        "max_time_ms_small_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": 1000,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS=1000 should succeed",
    ),
    CommandTestCase(
        "max_time_ms_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": INT32_MAX,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS at int32 maximum should succeed",
    ),
    CommandTestCase(
        "max_time_ms_double_whole",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": 1000.0,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS as whole-number double should succeed",
    ),
    CommandTestCase(
        "max_time_ms_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": Int64(INT32_MAX),
        },
        expected={"ok": 1.0},
        msg="maxTimeMS as Int64 at int32 max should succeed",
    ),
    CommandTestCase(
        "max_time_ms_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": Decimal128("1000"),
        },
        expected={"ok": 1.0},
        msg="maxTimeMS as Decimal128 should succeed",
    ),
    CommandTestCase(
        "max_time_ms_double_neg_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": DOUBLE_NEGATIVE_ZERO,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS=-0.0 should be treated as 0",
    ),
    CommandTestCase(
        "max_time_ms_decimal128_neg_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS=Decimal128('-0') should be treated as 0",
    ),
    CommandTestCase(
        "max_time_ms_double_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": DOUBLE_ZERO,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS=0.0 should succeed",
    ),
    CommandTestCase(
        "max_time_ms_decimal128_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": DECIMAL128_ZERO,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS=Decimal128('0') should succeed",
    ),
    CommandTestCase(
        "max_time_ms_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": None,
        },
        expected={"ok": 1.0},
        msg="maxTimeMS=null should succeed",
    ),
]

# Property [maxTimeMS Type Errors]: non-numeric types produce a
# TypeMismatch error.
RENAME_MAX_TIME_MS_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"max_time_ms_type_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"maxTimeMS as {tid} should produce TypeMismatch",
    )
    for tid, val in [
        ("string", "hello"),
        ("bool", True),
        ("array", [1]),
        ("object", {"a": 1}),
        ("objectid", ObjectId()),
        ("binary", Binary(b"x")),
        ("regex", Regex("a")),
        ("timestamp", Timestamp(1, 1)),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [maxTimeMS Value Errors]: numeric values that are negative
# or exceed int32 range produce a BadValue error; fractional or
# non-finite values produce a FailedToParse error.
RENAME_MAX_TIME_MS_VALUE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_time_ms_negative_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": -1,
        },
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS=-1 should produce BadValue",
    ),
    CommandTestCase(
        "max_time_ms_negative_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": -1.0,
        },
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS=-1.0 should produce BadValue",
    ),
    CommandTestCase(
        "max_time_ms_negative_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": Decimal128("-1"),
        },
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS=Decimal128('-1') should produce BadValue",
    ),
    CommandTestCase(
        "max_time_ms_exceeds_int32_max_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": Int64(INT32_OVERFLOW),
        },
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS as Int64 exceeding int32 max should produce BadValue",
    ),
    CommandTestCase(
        "max_time_ms_exceeds_int32_max_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": float(INT32_OVERFLOW),
        },
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS as double exceeding int32 max should produce BadValue",
    ),
    CommandTestCase(
        "max_time_ms_fractional_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": 1.5,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS=1.5 (fractional double) should produce FailedToParse",
    ),
    CommandTestCase(
        "max_time_ms_fractional_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": Decimal128("99999.5"),
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS=Decimal128 fractional should produce FailedToParse",
    ),
    CommandTestCase(
        "max_time_ms_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": FLOAT_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS=NaN should produce FailedToParse",
    ),
    CommandTestCase(
        "max_time_ms_neg_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": FLOAT_NEGATIVE_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS=negative NaN should produce FailedToParse",
    ),
    CommandTestCase(
        "max_time_ms_decimal128_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": DECIMAL128_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS=Decimal128('NaN') should produce FailedToParse",
    ),
    CommandTestCase(
        "max_time_ms_decimal128_neg_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": DECIMAL128_NEGATIVE_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS=Decimal128 negative NaN should produce FailedToParse",
    ),
    CommandTestCase(
        "max_time_ms_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": FLOAT_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS=Infinity should produce FailedToParse",
    ),
    CommandTestCase(
        "max_time_ms_decimal128_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": DECIMAL128_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS=Decimal128('Infinity') should produce FailedToParse",
    ),
    CommandTestCase(
        "max_time_ms_neg_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": FLOAT_NEGATIVE_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS=-Infinity should produce FailedToParse",
    ),
    CommandTestCase(
        "max_time_ms_decimal128_neg_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "maxTimeMS": DECIMAL128_NEGATIVE_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS=Decimal128('-Infinity') should produce FailedToParse",
    ),
]

RENAME_MAX_TIME_MS_TESTS: list[CommandTestCase] = (
    RENAME_MAX_TIME_MS_SUCCESS_TESTS
    + RENAME_MAX_TIME_MS_TYPE_ERROR_TESTS
    + RENAME_MAX_TIME_MS_VALUE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_MAX_TIME_MS_TESTS))
def test_renameCollection_max_time_ms(database_client, collection, register_db_cleanup, test):
    """Test renameCollection maxTimeMS parameter validation."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cross_db_cleanup_ns(cmd, ctx, register_db_cleanup)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
