"""Tests for the create command max parameter."""

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
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_OVERFLOW,
)

# Property [Max Type Acceptance]: the max field accepts int32, Int64, double,
# and Decimal128 numeric types; null is treated as omitted.
CREATE_MAX_TYPE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="max_int32",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": 100,
        },
        expected={"ok": 1.0},
        msg="int32 max should succeed",
    ),
    CommandTestCase(
        id="max_int64",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": Int64(100),
        },
        expected={"ok": 1.0},
        msg="Int64 max should succeed",
    ),
    CommandTestCase(
        id="max_double",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": 100.0,
        },
        expected={"ok": 1.0},
        msg="double max should succeed",
    ),
    CommandTestCase(
        id="max_decimal128",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": Decimal128("100"),
        },
        expected={"ok": 1.0},
        msg="Decimal128 max should succeed",
    ),
    CommandTestCase(
        id="max_null_treated_as_omitted",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": None,
        },
        expected={"ok": 1.0},
        msg="null max is treated as omitted",
    ),
    CommandTestCase(
        id="max_upper_bound",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": INT32_MAX,
        },
        expected={"ok": 1.0},
        msg="max at upper bound should succeed",
    ),
]

# Property [Max Coercion]: doubles truncate toward zero; Decimal128 uses
# banker's rounding; values <= 0 after coercion are treated as unlimited.
CREATE_MAX_COERCION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="max_double_truncation",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": 100.9,
        },
        expected={"ok": 1.0},
        msg="double 100.9 truncates toward zero to 100",
    ),
    CommandTestCase(
        id="max_decimal128_bankers_rounding",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": Decimal128("100.5"),
        },
        expected={"ok": 1.0},
        msg="Decimal128('100.5') banker's rounds to 100",
    ),
    CommandTestCase(
        id="max_zero_stored_as_unlimited",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": 0,
        },
        expected={"ok": 1.0},
        msg="max=0 stored as unlimited sentinel",
    ),
    CommandTestCase(
        id="max_negative_stored_as_unlimited",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": -5,
        },
        expected={"ok": 1.0},
        msg="max=-5 (negative) stored as unlimited sentinel",
    ),
    CommandTestCase(
        id="max_nan_double_stored_as_unlimited",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": FLOAT_NAN,
        },
        expected={"ok": 1.0},
        msg="NaN coerces to 0, stored as unlimited",
    ),
    CommandTestCase(
        id="max_nan_decimal128_stored_as_unlimited",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": DECIMAL128_NAN,
        },
        expected={"ok": 1.0},
        msg="Decimal128 NaN coerces to 0, stored as unlimited",
    ),
    CommandTestCase(
        id="max_negative_nan_double_stored_as_unlimited",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": FLOAT_NEGATIVE_NAN,
        },
        expected={"ok": 1.0},
        msg="-NaN coerces to 0, stored as unlimited",
    ),
    CommandTestCase(
        id="max_negative_nan_decimal128_stored_as_unlimited",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": DECIMAL128_NEGATIVE_NAN,
        },
        expected={"ok": 1.0},
        msg="Decimal128 -NaN coerces to 0, stored as unlimited",
    ),
    CommandTestCase(
        id="max_neg_infinity_stored_as_unlimited",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": FLOAT_NEGATIVE_INFINITY,
        },
        expected={"ok": 1.0},
        msg="-Infinity coerces to negative, stored as unlimited",
    ),
    CommandTestCase(
        id="max_decimal128_neg_infinity_stored_as_unlimited",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": DECIMAL128_NEGATIVE_INFINITY,
        },
        expected={"ok": 1.0},
        msg="Decimal128 -Infinity coerces to negative, stored as unlimited",
    ),
    CommandTestCase(
        id="max_double_at_boundary_truncates_ok",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": 2_147_483_647.9,
        },
        expected={"ok": 1.0},
        msg="double at boundary truncates toward zero to valid upper bound",
    ),
]

# Property [Max Type Strictness]: non-numeric types (including bool) for the
# max field produce TYPE_MISMATCH_ERROR.
CREATE_MAX_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"max_{tid}",
        command=lambda ctx, v=val, t=tid: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{tid} for max should fail with type mismatch",
    )
    for tid, val in [
        ("bool_true", True),
        ("bool_false", False),
        ("string", "100"),
        ("array", [100]),
        ("object", {"a": 1}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("binary", Binary(b"x")),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Max Overflow Rejection]: values >= 2147483648 after coercion
# (including Infinity and Decimal128 banker's rounding at the boundary)
# produce BAD_VALUE_ERROR.
CREATE_MAX_OVERFLOW_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="max_at_overflow_boundary",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": INT32_OVERFLOW,
        },
        error_code=BAD_VALUE_ERROR,
        msg="max at overflow boundary should fail",
    ),
    CommandTestCase(
        id="max_decimal128_rounds_to_overflow",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": Decimal128("2147483647.5"),
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 banker's rounds up to overflow boundary",
    ),
    CommandTestCase(
        id="max_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": FLOAT_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Infinity coerced to INT64_MAX exceeds upper bound",
    ),
    CommandTestCase(
        id="max_decimal128_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": DECIMAL128_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 Infinity coerced to INT64_MAX exceeds upper bound",
    ),
]

CREATE_MAX_TESTS: list[CommandTestCase] = (
    CREATE_MAX_TYPE_ACCEPTANCE_TESTS
    + CREATE_MAX_COERCION_TESTS
    + CREATE_MAX_TYPE_ERROR_TESTS
    + CREATE_MAX_OVERFLOW_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_MAX_TESTS))
def test_create_max(database_client, collection, test):
    """Test create command max behavior."""
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
