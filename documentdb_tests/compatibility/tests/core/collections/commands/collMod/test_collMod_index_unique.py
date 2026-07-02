"""Tests for collMod index unique conversion."""

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
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CANNOT_CONVERT_INDEX_TO_UNIQUE_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, NotExists
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_ZERO,
)

# Property [Index unique Truthy Conversion]: on an index with prepareUnique
# already committed and no duplicate entries, a bool true or any numeric type
# that coerces to true (any nonzero value, including negatives, NaN, and
# Infinity) converts the index to unique and echoes unique_new true.
COLLMOD_INDEX_UNIQUE_TRUTHY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"unique_truthy_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1", prepareUnique=True)],
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "unique": v},
        },
        expected={"ok": Eq(1.0), "unique_new": Eq(True), "unique_old": NotExists()},
        msg=f"collMod should coerce a {tid} unique value to true and convert the index",
    )
    for tid, val in [
        ("bool_true", True),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("int32_negative", -1),
        ("double_negative", -2.0),
        ("decimal128_negative", Decimal128("-1")),
        ("float_nan", FLOAT_NAN),
        ("decimal128_nan", DECIMAL128_NAN),
        ("float_infinity", FLOAT_INFINITY),
        ("decimal128_infinity", DECIMAL128_INFINITY),
        ("float_negative_infinity", FLOAT_NEGATIVE_INFINITY),
        ("decimal128_negative_infinity", DECIMAL128_NEGATIVE_INFINITY),
    ]
]

# Property [Index unique Already Unique No-Op]: setting unique true on an index
# that is already unique is an accepted no-op that omits unique_old and
# unique_new from the result.
COLLMOD_INDEX_UNIQUE_NO_OP_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unique_already_unique",
        indexes=[IndexModel([("a", 1)], name="a_1", unique=True)],
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "unique": True},
        },
        expected={
            "ok": Eq(1.0),
            "unique_old": NotExists(),
            "unique_new": NotExists(),
        },
        msg="collMod should accept unique true on an already-unique index as a no-op",
    ),
]

# Property [Index unique Non-Bool-Non-Numeric Rejection]: a type outside bool
# and the numeric types for index.unique produces a type-mismatch error.
COLLMOD_INDEX_UNIQUE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"unique_type_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1", prepareUnique=True)],
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "unique": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} unique value as a type mismatch",
    )
    for tid, val in [
        ("string", "true"),
        ("array", [True]),
        ("object", {"x": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Index unique Null Rejection]: a null index.unique is treated as
# absent, leaving no modification field, and is rejected as an invalid option.
COLLMOD_INDEX_UNIQUE_NULL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unique_null",
        indexes=[IndexModel([("a", 1)], name="a_1", prepareUnique=True)],
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "unique": None},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should treat a null unique value as absent and reject it as an invalid "
        "option",
    ),
]

# Property [Index unique True Without prepareUnique Rejection]: a truthy unique
# value on an index that has no committed prepareUnique is rejected as an invalid
# option, since the conversion requires prepareUnique to be set first.
COLLMOD_INDEX_UNIQUE_NO_PREPARE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unique_true_no_prepare",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "unique": True},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a truthy unique value without a prior prepareUnique "
        "as an invalid option",
    ),
]

# Property [Index unique Falsy Rejection]: a falsy unique value (bool false or
# any numeric zero) attempts to make the index non-unique, which is unsupported,
# and is rejected as a bad value.
COLLMOD_INDEX_UNIQUE_FALSY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"unique_falsy_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "unique": v},
        },
        error_code=BAD_VALUE_ERROR,
        msg=f"collMod should reject a {tid} falsy unique value as a bad value",
    )
    for tid, val in [
        ("bool_false", False),
        ("int32_zero", 0),
        ("int64_zero", INT64_ZERO),
        ("double_zero", DOUBLE_ZERO),
        ("double_negative_zero", DOUBLE_NEGATIVE_ZERO),
        ("decimal128_zero", DECIMAL128_ZERO),
        ("decimal128_negative_zero", DECIMAL128_NEGATIVE_ZERO),
    ]
]

# Property [Index unique Conversion With Duplicates Rejection]: the conversion
# workflow of prepareUnique then unique true on an index whose data contains
# duplicate entries cannot convert and is rejected as a cannot-convert error.
COLLMOD_INDEX_UNIQUE_CONVERT_DUP_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unique_convert_with_duplicates",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 1}],
        setup=lambda coll: execute_command(
            coll,
            {"collMod": coll.name, "index": {"name": "a_1", "prepareUnique": True}},
        ),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "unique": True},
        },
        error_code=CANNOT_CONVERT_INDEX_TO_UNIQUE_ERROR,
        msg="collMod should reject a unique conversion on an index with duplicate entries",
    ),
]

COLLMOD_INDEX_UNIQUE_TESTS: list[CommandTestCase] = (
    COLLMOD_INDEX_UNIQUE_TRUTHY_TESTS
    + COLLMOD_INDEX_UNIQUE_NO_OP_TESTS
    + COLLMOD_INDEX_UNIQUE_TYPE_ERROR_TESTS
    + COLLMOD_INDEX_UNIQUE_NULL_ERROR_TESTS
    + COLLMOD_INDEX_UNIQUE_NO_PREPARE_ERROR_TESTS
    + COLLMOD_INDEX_UNIQUE_FALSY_ERROR_TESTS
    + COLLMOD_INDEX_UNIQUE_CONVERT_DUP_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_INDEX_UNIQUE_TESTS))
def test_collMod_index_unique(database_client, collection, test):
    """Test collMod index unique conversion acceptance and rejection."""
    collection = test.prepare(database_client, collection)
    if test.setup:
        test.setup(collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
