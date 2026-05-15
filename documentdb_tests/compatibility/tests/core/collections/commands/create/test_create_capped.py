"""Tests for the create command capped parameter."""

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
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
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
    INT64_ZERO,
)

# Property [Capped Truthiness]: non-zero numeric values (including NaN,
# Infinity, negatives, and fractions) are truthy for the capped field and
# create a capped collection when paired with size.
CREATE_CAPPED_TRUTHY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="capped_true_with_size",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="capped:true + valid size should create capped collection",
    ),
    CommandTestCase(
        id="capped_int32_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": 42,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="int32 truthy value for capped should succeed",
    ),
    CommandTestCase(
        id="capped_int64_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": Int64(1),
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="Int64 truthy value for capped should succeed",
    ),
    CommandTestCase(
        id="capped_double_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": 3.14,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="double truthy value for capped should succeed",
    ),
    CommandTestCase(
        id="capped_decimal128_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": Decimal128("1"),
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="Decimal128 truthy value for capped should succeed",
    ),
    CommandTestCase(
        id="capped_nan_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": FLOAT_NAN,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="NaN is truthy for capped",
    ),
    CommandTestCase(
        id="capped_negative_nan_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": FLOAT_NEGATIVE_NAN,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="-NaN is truthy for capped",
    ),
    CommandTestCase(
        id="capped_decimal128_nan_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": DECIMAL128_NAN,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="Decimal128 NaN is truthy for capped",
    ),
    CommandTestCase(
        id="capped_decimal128_negative_nan_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": DECIMAL128_NEGATIVE_NAN,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="Decimal128 -NaN is truthy for capped",
    ),
    CommandTestCase(
        id="capped_infinity_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": FLOAT_INFINITY,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="Infinity is truthy for capped",
    ),
    CommandTestCase(
        id="capped_neg_infinity_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": FLOAT_NEGATIVE_INFINITY,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="-Infinity is truthy for capped",
    ),
    CommandTestCase(
        id="capped_decimal128_infinity_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": DECIMAL128_INFINITY,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="Decimal128 Infinity is truthy for capped",
    ),
    CommandTestCase(
        id="capped_decimal128_neg_infinity_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": DECIMAL128_NEGATIVE_INFINITY,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="Decimal128 -Infinity is truthy for capped",
    ),
    CommandTestCase(
        id="capped_negative_number_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": -5,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="Negative number is truthy for capped",
    ),
    CommandTestCase(
        id="capped_fraction_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": 0.5,
            "size": 4096,
        },
        expected={"ok": 1.0},
        msg="Fraction is truthy for capped",
    ),
]

# Property [Capped Falsy]: zero values across all numeric types are falsy
# for the capped field and create a regular collection without requiring size.
CREATE_CAPPED_FALSY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="capped_zero_int_falsy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": 0,
        },
        expected={"ok": 1.0},
        msg="capped=0 is falsy, creates regular collection",
    ),
    CommandTestCase(
        id="capped_zero_float_falsy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": DOUBLE_ZERO,
        },
        expected={"ok": 1.0},
        msg="capped=0.0 is falsy, creates regular collection",
    ),
    CommandTestCase(
        id="capped_neg_zero_falsy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": DOUBLE_NEGATIVE_ZERO,
        },
        expected={"ok": 1.0},
        msg="capped=-0.0 is falsy, creates regular collection",
    ),
    CommandTestCase(
        id="capped_int64_zero_falsy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": INT64_ZERO,
        },
        expected={"ok": 1.0},
        msg="capped=Int64(0) is falsy, creates regular collection",
    ),
    CommandTestCase(
        id="capped_decimal128_zero_falsy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": DECIMAL128_ZERO,
        },
        expected={"ok": 1.0},
        msg="capped=Decimal128('0') is falsy, creates regular collection",
    ),
    CommandTestCase(
        id="capped_decimal128_neg_zero_falsy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"ok": 1.0},
        msg="capped=Decimal128('-0') is falsy, creates regular collection",
    ),
]

# Property [Capped Compatibility]: capped collections accept max, validator,
# collation, storageEngine, and writeConcern alongside capped:true and size.
CREATE_CAPPED_COMPATIBILITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="capped_with_max",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "max": 100,
        },
        expected={"ok": 1.0},
        msg="capped:true + size + max should succeed",
    ),
    CommandTestCase(
        id="capped_with_validator",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "validator": {"x": {"$exists": True}},
        },
        expected={"ok": 1.0},
        msg="capped:true + size + validator should succeed",
    ),
    CommandTestCase(
        id="capped_with_collation",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="capped:true + size + collation should succeed",
    ),
    CommandTestCase(
        id="capped_with_storage_engine",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "storageEngine": {"wiredTiger": {"configString": ""}},
        },
        expected={"ok": 1.0},
        msg="capped:true + size + storageEngine should succeed",
    ),
    CommandTestCase(
        id="capped_with_write_concern",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "writeConcern": {"w": 1},
        },
        expected={"ok": 1.0},
        msg="capped:true + size + writeConcern should succeed",
    ),
]

# Property [Capped Type Strictness]: non-numeric and non-bool types for the
# capped field produce TYPE_MISMATCH_ERROR.
CREATE_CAPPED_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"capped_{tid}",
        command=lambda ctx, v=val, t=tid: {
            "create": f"{ctx.collection}_custom",
            "capped": v,
            "size": 4096,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{tid} capped should fail with type mismatch",
    )
    for tid, val in [
        ("string", "yes"),
        ("array", [1]),
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

# Property [Capped Null Treated as Missing]: null for the capped field is
# treated as missing, so size without capped triggers INVALID_OPTIONS_ERROR.
CREATE_CAPPED_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="capped_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": None,
            "size": 4096,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="null capped is treated as missing; size without capped triggers error",
    ),
]

# Property [Capped Required Fields]: capped:true without size, size without
# capped:true, max without capped:true, and capped:false with size all
# produce INVALID_OPTIONS_ERROR.
CREATE_CAPPED_REQUIRED_FIELDS_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="capped_true_without_size",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="capped:true without size should fail",
    ),
    CommandTestCase(
        id="size_without_capped",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "size": 4096,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="size without capped:true should fail",
    ),
    CommandTestCase(
        id="max_without_capped",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "max": 100,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="max without capped:true should fail",
    ),
    CommandTestCase(
        id="capped_false_with_size",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": False,
            "size": 4096,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="capped:false + size should fail (size NOT ignored for non-capped)",
    ),
    CommandTestCase(
        id="capped_true_no_size_with_viewon",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "viewOn": ctx.collection,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="capped:true without size fires before viewOn processing",
    ),
]

CREATE_CAPPED_TESTS: list[CommandTestCase] = (
    CREATE_CAPPED_TRUTHY_TESTS
    + CREATE_CAPPED_FALSY_TESTS
    + CREATE_CAPPED_COMPATIBILITY_TESTS
    + CREATE_CAPPED_TYPE_ERROR_TESTS
    + CREATE_CAPPED_NULL_TESTS
    + CREATE_CAPPED_REQUIRED_FIELDS_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_CAPPED_TESTS))
def test_create_capped(database_client, collection, test):
    """Test create command capped behavior."""
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
