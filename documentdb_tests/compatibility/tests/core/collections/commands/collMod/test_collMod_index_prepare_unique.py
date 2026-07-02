"""Tests for collMod index prepareUnique and its combination rule."""

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

# Property [Index prepareUnique Truthy Coercion]: a bool true or any numeric type
# that coerces to true (any nonzero value, including negatives, NaN, and
# Infinity) sets prepareUnique on an index that does not have it, echoing
# prepareUnique_old false and prepareUnique_new true, despite the docs describing
# the field as boolean-only.
COLLMOD_INDEX_PREPARE_UNIQUE_TRUTHY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"prepare_unique_truthy_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "prepareUnique": v},
        },
        expected={
            "ok": Eq(1.0),
            "prepareUnique_old": Eq(False),
            "prepareUnique_new": Eq(True),
        },
        msg=f"collMod should coerce a {tid} prepareUnique value to true and echo the change",
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

# Property [Index prepareUnique Falsy Coercion]: any numeric zero (including
# negative zero) coerces to false, so applying it to an index that does not have
# prepareUnique does not change the state and the result omits prepareUnique_old
# and prepareUnique_new.
COLLMOD_INDEX_PREPARE_UNIQUE_FALSY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"prepare_unique_falsy_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "prepareUnique": v},
        },
        expected={
            "ok": Eq(1.0),
            "prepareUnique_old": NotExists(),
            "prepareUnique_new": NotExists(),
        },
        msg=f"collMod should coerce a {tid} prepareUnique value to false, leaving the state "
        "unchanged",
    )
    for tid, val in [
        ("int32_zero", 0),
        ("int64_zero", INT64_ZERO),
        ("double_zero", DOUBLE_ZERO),
        ("double_negative_zero", DOUBLE_NEGATIVE_ZERO),
        ("decimal128_zero", DECIMAL128_ZERO),
        ("decimal128_negative_zero", DECIMAL128_NEGATIVE_ZERO),
    ]
]

# Property [Index prepareUnique Unchanged State]: setting prepareUnique to its
# current value (re-setting an index that already has prepareUnique or clearing
# one that does not) does not change the state, so the result omits
# prepareUnique_old and prepareUnique_new, while a genuine state change echoes
# both.
COLLMOD_INDEX_PREPARE_UNIQUE_UNCHANGED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "prepare_unique_already_set",
        indexes=[IndexModel([("a", 1)], name="a_1", prepareUnique=True)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "prepareUnique": True},
        },
        expected={
            "ok": Eq(1.0),
            "prepareUnique_old": NotExists(),
            "prepareUnique_new": NotExists(),
        },
        msg="collMod should omit prepareUnique_old and prepareUnique_new when re-setting an "
        "already-prepareUnique index",
    ),
    CommandTestCase(
        "prepare_unique_already_unset",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "prepareUnique": False},
        },
        expected={
            "ok": Eq(1.0),
            "prepareUnique_old": NotExists(),
            "prepareUnique_new": NotExists(),
        },
        msg="collMod should omit prepareUnique_old and prepareUnique_new when clearing an index "
        "that has no prepareUnique",
    ),
    CommandTestCase(
        "prepare_unique_clear_changes",
        indexes=[IndexModel([("a", 1)], name="a_1", prepareUnique=True)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "prepareUnique": False},
        },
        expected={
            "ok": Eq(1.0),
            "prepareUnique_old": Eq(True),
            "prepareUnique_new": Eq(False),
        },
        msg="collMod should echo the change when clearing prepareUnique on an index that has it",
    ),
]

# Property [Index Field Combination prepareUnique No-Change]: a prepareUnique
# value that does not change the index state may be combined with another
# modification field, since the cannot-be-combined rule is gated on an actual
# prepareUnique state change, so the other field applies and prepareUnique_old
# and prepareUnique_new are omitted.
COLLMOD_INDEX_COMBO_PREPARE_UNIQUE_NO_CHANGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "combo_prepare_unique_unset_no_change_with_hidden",
        indexes=[IndexModel([("a", 1)], name="a_1", hidden=False)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "prepareUnique": False, "hidden": True},
        },
        expected={
            "ok": Eq(1.0),
            "hidden_old": Eq(False),
            "hidden_new": Eq(True),
            "prepareUnique_old": NotExists(),
            "prepareUnique_new": NotExists(),
        },
        msg="collMod should allow a no-change prepareUnique combined with a hidden change",
    ),
    CommandTestCase(
        "combo_prepare_unique_set_no_change_with_hidden",
        indexes=[IndexModel([("a", 1)], name="a_1", prepareUnique=True, hidden=False)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "prepareUnique": True, "hidden": True},
        },
        expected={
            "ok": Eq(1.0),
            "hidden_old": Eq(False),
            "hidden_new": Eq(True),
            "prepareUnique_old": NotExists(),
            "prepareUnique_new": NotExists(),
        },
        msg="collMod should allow a no-change prepareUnique combined with a hidden change",
    ),
]

# Property [Index prepareUnique Non-Bool-Non-Numeric Rejection]: a type outside
# bool and the numeric types for index.prepareUnique produces a type-mismatch
# error.
COLLMOD_INDEX_PREPARE_UNIQUE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"prepare_unique_type_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "prepareUnique": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} prepareUnique value as a type mismatch",
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

# Property [Index prepareUnique Null Rejection]: a null index.prepareUnique is
# treated as absent, leaving no modification field, and is rejected as an
# invalid option.
COLLMOD_INDEX_PREPARE_UNIQUE_NULL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "prepare_unique_null",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "prepareUnique": None},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should treat a null prepareUnique value as absent and reject it as an "
        "invalid option",
    ),
]

# Property [Index Field Combination prepareUnique Change Rejection]: a prepareUnique
# change combined with any other index modification field is rejected as an
# invalid option, since a prepareUnique state change cannot be combined with
# another modification.
COLLMOD_INDEX_COMBO_PREPARE_UNIQUE_CHANGE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "combo_prepare_unique_change_with_hidden",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "prepareUnique": True, "hidden": True},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a prepareUnique change combined with a hidden change "
        "as an invalid option",
    ),
    CommandTestCase(
        "combo_prepare_unique_change_with_expire",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "prepareUnique": True, "expireAfterSeconds": 100},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a prepareUnique change combined with an expireAfterSeconds "
        "change as an invalid option",
    ),
]

COLLMOD_INDEX_PREPARE_UNIQUE_TESTS: list[CommandTestCase] = (
    COLLMOD_INDEX_PREPARE_UNIQUE_TRUTHY_TESTS
    + COLLMOD_INDEX_PREPARE_UNIQUE_FALSY_TESTS
    + COLLMOD_INDEX_PREPARE_UNIQUE_UNCHANGED_TESTS
    + COLLMOD_INDEX_COMBO_PREPARE_UNIQUE_NO_CHANGE_TESTS
    + COLLMOD_INDEX_PREPARE_UNIQUE_TYPE_ERROR_TESTS
    + COLLMOD_INDEX_PREPARE_UNIQUE_NULL_ERROR_TESTS
    + COLLMOD_INDEX_COMBO_PREPARE_UNIQUE_CHANGE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_INDEX_PREPARE_UNIQUE_TESTS))
def test_collMod_index_prepare_unique(database_client, collection, test):
    """Test collMod index prepareUnique acceptance, rejection, and combination rule."""
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
