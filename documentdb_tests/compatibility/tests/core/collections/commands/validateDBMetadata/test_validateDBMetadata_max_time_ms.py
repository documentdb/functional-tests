"""Tests for validateDBMetadata maxTimeMS acceptance and errors."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
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
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
)

# Property [maxTimeMS Acceptance (Smoke)]: integral numeric values within
# the valid range are accepted regardless of BSON numeric type.
VALIDATE_DB_METADATA_MAX_TIME_MS_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_time_ms_zero_int32",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": 0,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept maxTimeMS of 0 as int32",
    ),
    CommandTestCase(
        "max_time_ms_max_int32",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": INT32_MAX,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept maxTimeMS at int32 max",
    ),
    CommandTestCase(
        "max_time_ms_int64",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": Int64(1000),
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept maxTimeMS as Int64",
    ),
    CommandTestCase(
        "max_time_ms_double",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": 500.0,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept maxTimeMS as integral double",
    ),
    CommandTestCase(
        "max_time_ms_decimal128",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": Decimal128("100"),
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept maxTimeMS as Decimal128",
    ),
    CommandTestCase(
        "max_time_ms_neg_zero_double",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": DOUBLE_NEGATIVE_ZERO,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept maxTimeMS of -0.0 as zero",
    ),
    CommandTestCase(
        "max_time_ms_neg_zero_decimal128",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept maxTimeMS of Decimal128 -0 as zero",
    ),
    CommandTestCase(
        "max_time_ms_decimal128_trailing_zeros_one",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": Decimal128("1000.0"),
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept Decimal128 with one trailing zero",
    ),
    CommandTestCase(
        "max_time_ms_decimal128_trailing_zeros_two",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": Decimal128("5000.00"),
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept Decimal128 with two trailing zeros",
    ),
]

# Property [maxTimeMS Errors (Smoke)]: non-integral or out-of-range
# numeric values and non-numeric types are rejected.
VALIDATE_DB_METADATA_MAX_TIME_MS_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"max_time_ms_err_{tid}",
            command={
                "validateDBMetadata": 1,
                "apiParameters": {"version": "1", "strict": True},
                "maxTimeMS": val,
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"validateDBMetadata should reject {tid} maxTimeMS",
        )
        for tid, val in [
            ("string", "1000"),
            ("bool", True),
            ("array", [100]),
            ("object", {"ms": 100}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"data")),
            ("regex", Regex(".*")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        "max_time_ms_err_fractional_double",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": 100.5,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="validateDBMetadata should reject fractional double maxTimeMS",
    ),
    CommandTestCase(
        "max_time_ms_err_fractional_decimal128",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": DECIMAL128_ONE_AND_HALF,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="validateDBMetadata should reject fractional Decimal128 maxTimeMS",
    ),
    CommandTestCase(
        "max_time_ms_err_nan_double",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": FLOAT_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="validateDBMetadata should reject NaN double maxTimeMS",
    ),
    CommandTestCase(
        "max_time_ms_err_nan_decimal128",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": DECIMAL128_NAN,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="validateDBMetadata should reject NaN Decimal128 maxTimeMS",
    ),
    CommandTestCase(
        "max_time_ms_err_infinity_double",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": FLOAT_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="validateDBMetadata should reject Infinity double maxTimeMS",
    ),
    CommandTestCase(
        "max_time_ms_err_neg_infinity_double",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": FLOAT_NEGATIVE_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="validateDBMetadata should reject -Infinity double maxTimeMS",
    ),
    CommandTestCase(
        "max_time_ms_err_neg_infinity_decimal128",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": DECIMAL128_NEGATIVE_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="validateDBMetadata should reject -Infinity Decimal128 maxTimeMS",
    ),
    CommandTestCase(
        "max_time_ms_err_pos_infinity_decimal128",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": DECIMAL128_INFINITY,
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="validateDBMetadata should reject +Infinity Decimal128 maxTimeMS",
    ),
    CommandTestCase(
        "max_time_ms_err_negative_int32",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": -1,
        },
        error_code=BAD_VALUE_ERROR,
        msg="validateDBMetadata should reject negative int32 maxTimeMS",
    ),
    CommandTestCase(
        "max_time_ms_err_negative_int64",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": Int64(-100),
        },
        error_code=BAD_VALUE_ERROR,
        msg="validateDBMetadata should reject negative Int64 maxTimeMS",
    ),
    CommandTestCase(
        "max_time_ms_err_above_int32_max",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": Int64(INT32_MAX + 1),
        },
        error_code=BAD_VALUE_ERROR,
        msg="validateDBMetadata should reject value above int32 max",
    ),
]

VALIDATE_DB_METADATA_MAX_TIME_MS_TESTS: list[CommandTestCase] = (
    VALIDATE_DB_METADATA_MAX_TIME_MS_ACCEPTANCE_TESTS + VALIDATE_DB_METADATA_MAX_TIME_MS_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VALIDATE_DB_METADATA_MAX_TIME_MS_TESTS))
def test_validateDBMetadata_max_time_ms(database_client, collection, test):
    """Test validateDBMetadata maxTimeMS acceptance and errors."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
