"""Tests for the create command size parameter."""

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
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

# Property [Size Type Acceptance]: the size field accepts int32, Int64, double,
# and Decimal128 numeric types.
CREATE_SIZE_TYPE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="size_int32",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="int32 size should succeed",
    ),
    CommandTestCase(
        id="size_int64",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": Int64(4096),
        },
        expected={"ok": 1.0},
        msg="Int64 size should succeed",
    ),
    CommandTestCase(
        id="size_double",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096.0,
        },
        expected={"ok": 1.0},
        msg="double size should succeed",
    ),
    CommandTestCase(
        id="size_decimal128",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": Decimal128("4096"),
        },
        expected={"ok": 1.0},
        msg="Decimal128 size should succeed",
    ),
]

# Property [Size Range Boundaries]: the valid range is [1, 2^50] inclusive.
CREATE_SIZE_RANGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="size_minimum_1",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 1,
        },
        expected={"ok": 1.0},
        msg="size=1 (minimum valid value) should succeed",
    ),
    CommandTestCase(
        id="size_maximum_2_pow_50",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": Int64(1_125_899_906_842_624),
        },
        expected={"ok": 1.0},
        msg="size=2^50 (maximum valid value) should succeed",
    ),
]

# Property [Size Coercion]: doubles truncate toward zero and Decimal128 values
# use banker's rounding before range validation.
CREATE_SIZE_COERCION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="size_double_truncation_toward_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 1.9,
        },
        expected={"ok": 1.0},
        msg="double 1.9 truncates toward zero to 1, which is valid",
    ),
    CommandTestCase(
        id="size_decimal128_bankers_rounding_1_5",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": DECIMAL128_ONE_AND_HALF,
        },
        expected={"ok": 1.0},
        msg="Decimal128('1.5') banker's rounds to 2, which is valid",
    ),
    CommandTestCase(
        id="size_decimal128_bankers_rounding_2_5",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": DECIMAL128_TWO_AND_HALF,
        },
        expected={"ok": 1.0},
        msg="Decimal128('2.5') banker's rounds to 2, which is valid",
    ),
    CommandTestCase(
        id="size_decimal128_bankers_rounding_3_5",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": Decimal128("3.5"),
        },
        expected={"ok": 1.0},
        msg="Decimal128('3.5') banker's rounds to 4, which is valid",
    ),
]

# Property [Size Type Strictness]: non-numeric types (including bool) for the
# size field produce TYPE_MISMATCH_ERROR.
CREATE_SIZE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"size_{tid}",
        command=lambda ctx, v=val, t=tid: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{tid} for size should fail with type mismatch",
    )
    for tid, val in [
        ("bool_true", True),
        ("bool_false", False),
        ("string", "4096"),
        ("object", {"a": 1}),
        ("array", [4096]),
        ("binary", Binary(b"x")),
        ("objectid", ObjectId()),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
    ]
]

# Property [Size Null Treated as Missing]: null size with capped=True is treated
# as missing, producing INVALID_OPTIONS_ERROR.
CREATE_SIZE_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="size_null_treated_as_missing",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": None,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="null size treated as missing when capped=True",
    ),
]

# Property [Size Value Rejection]: values that coerce to < 1 or > 2^50
# (including zero, negatives, NaN, and Infinity) produce BAD_VALUE_ERROR.
CREATE_SIZE_VALUE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="size_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 0,
        },
        error_code=BAD_VALUE_ERROR,
        msg="size=0 is < 1 after coercion",
    ),
    CommandTestCase(
        id="size_double_truncates_to_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 0.9,
        },
        error_code=BAD_VALUE_ERROR,
        msg="double 0.9 truncates toward zero to 0, which is < 1",
    ),
    CommandTestCase(
        id="size_negative",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": -1,
        },
        error_code=BAD_VALUE_ERROR,
        msg="negative size is < 1",
    ),
    CommandTestCase(
        id="size_decimal128_rounds_to_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": DECIMAL128_HALF,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128('0.5') banker's rounds to 0, which is < 1",
    ),
    CommandTestCase(
        id="size_exceeds_2_pow_50",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": Int64(1_125_899_906_842_625),
        },
        error_code=BAD_VALUE_ERROR,
        msg="size > 2^50 should fail",
    ),
    CommandTestCase(
        id="size_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": FLOAT_NAN,
        },
        error_code=BAD_VALUE_ERROR,
        msg="NaN coerced to 0, which is < 1",
    ),
    CommandTestCase(
        id="size_decimal128_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": DECIMAL128_NAN,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 NaN coerced to 0, which is < 1",
    ),
    CommandTestCase(
        id="size_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": FLOAT_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Infinity coerced to INT64_MAX, which is > 2^50",
    ),
    CommandTestCase(
        id="size_decimal128_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": DECIMAL128_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 Infinity coerced to INT64_MAX, which is > 2^50",
    ),
    CommandTestCase(
        id="size_negative_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": FLOAT_NEGATIVE_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="-Infinity coerced to negative value, which is < 1",
    ),
    CommandTestCase(
        id="size_decimal128_negative_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": DECIMAL128_NEGATIVE_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 -Infinity coerced to negative value, which is < 1",
    ),
    CommandTestCase(
        id="size_negative_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": FLOAT_NEGATIVE_NAN,
        },
        error_code=BAD_VALUE_ERROR,
        msg="-NaN coerced to 0, which is < 1",
    ),
    CommandTestCase(
        id="size_decimal128_negative_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": DECIMAL128_NEGATIVE_NAN,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 -NaN coerced to 0, which is < 1",
    ),
]

CREATE_SIZE_TESTS: list[CommandTestCase] = (
    CREATE_SIZE_TYPE_ACCEPTANCE_TESTS
    + CREATE_SIZE_RANGE_TESTS
    + CREATE_SIZE_COERCION_TESTS
    + CREATE_SIZE_TYPE_ERROR_TESTS
    + CREATE_SIZE_NULL_TESTS
    + CREATE_SIZE_VALUE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_SIZE_TESTS))
def test_create_size(database_client, collection, test):
    """Test create command size behavior."""
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
