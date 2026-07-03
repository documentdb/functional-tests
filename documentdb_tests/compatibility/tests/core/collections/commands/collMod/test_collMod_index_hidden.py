"""Tests for collMod index hidden."""

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
    INDEX_NOT_FOUND_ERROR,
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

# Property [Index hidden Truthy Coercion]: a bool true or any numeric type that
# coerces to true (any nonzero value, including negatives, NaN, and Infinity)
# sets hidden on a previously unhidden index, echoing hidden_old false and
# hidden_new true, despite the docs describing the field as boolean-only.
COLLMOD_INDEX_HIDDEN_TRUTHY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"hidden_truthy_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1", hidden=False)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "hidden": v},
        },
        expected={"ok": Eq(1.0), "hidden_old": Eq(False), "hidden_new": Eq(True)},
        msg=f"collMod should coerce a {tid} hidden value to true and echo the change",
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

# Property [Index hidden Falsy Coercion]: any numeric zero (including negative
# zero) coerces to false, so applying it to an already unhidden index does not
# change the state and the result omits hidden_old and hidden_new.
COLLMOD_INDEX_HIDDEN_FALSY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"hidden_falsy_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1", hidden=False)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "hidden": v},
        },
        expected={
            "ok": Eq(1.0),
            "hidden_old": NotExists(),
            "hidden_new": NotExists(),
        },
        msg=f"collMod should coerce a {tid} hidden value to false, leaving the state unchanged",
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

# Property [Index hidden Unchanged State]: setting hidden to its current value
# (hiding an already-hidden index or unhiding an already-unhidden index) does
# not change the state, so the result omits hidden_old and hidden_new, while a
# genuine state change echoes both.
COLLMOD_INDEX_HIDDEN_UNCHANGED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hidden_already_hidden",
        indexes=[IndexModel([("a", 1)], name="a_1", hidden=True)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "hidden": True},
        },
        expected={
            "ok": Eq(1.0),
            "hidden_old": NotExists(),
            "hidden_new": NotExists(),
        },
        msg="collMod should omit hidden_old and hidden_new when hiding an already-hidden index",
    ),
    CommandTestCase(
        "hidden_already_unhidden",
        indexes=[IndexModel([("a", 1)], name="a_1", hidden=False)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "hidden": False},
        },
        expected={
            "ok": Eq(1.0),
            "hidden_old": NotExists(),
            "hidden_new": NotExists(),
        },
        msg="collMod should omit hidden_old and hidden_new when unhiding an already-unhidden "
        "index",
    ),
    CommandTestCase(
        "hidden_unhide_changes",
        indexes=[IndexModel([("a", 1)], name="a_1", hidden=True)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "hidden": False},
        },
        expected={"ok": Eq(1.0), "hidden_old": Eq(True), "hidden_new": Eq(False)},
        msg="collMod should echo the change when unhiding a hidden index",
    ),
]

# Property [Index Id Index Hidden Rejection]: identifying the _id_ index by name
# or keyPattern for a hidden change is rejected as a bad value.
COLLMOD_INDEX_ID_HIDDEN_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "id_index_hidden_by_name",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "_id_", "hidden": True},
        },
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject hiding the _id_ index identified by name as a bad value",
    ),
    CommandTestCase(
        "id_index_hidden_by_key_pattern",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"keyPattern": {"_id": 1}, "hidden": True},
        },
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject hiding the _id_ index identified by keyPattern as a bad value",
    ),
]

# Property [Index hidden Non-Bool-Non-Numeric Rejection]: a type outside bool
# and the numeric types for index.hidden produces a type-mismatch error.
COLLMOD_INDEX_HIDDEN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"hidden_type_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1", hidden=False)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "hidden": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} hidden value as a type mismatch",
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

# Property [Index hidden Null Rejection]: a null index.hidden is treated as
# absent, leaving no modification field, and is rejected as an invalid option.
COLLMOD_INDEX_HIDDEN_NULL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hidden_null",
        indexes=[IndexModel([("a", 1)], name="a_1", hidden=False)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "hidden": None},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should treat a null hidden value as absent and reject it as an invalid option",
    ),
]

# Property [Index hidden Text Index Identification]: a text index can be hidden
# by name but not by keyPattern, because a text index stores a different stored
# key pattern, so identifying it by keyPattern is index-not-found.
COLLMOD_INDEX_HIDDEN_TEXT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hidden_text_index_by_key_pattern",
        indexes=[IndexModel([("a", "text")], name="a_text")],
        docs=[{"_id": 1, "a": "hello world"}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"keyPattern": {"a": "text"}, "hidden": True},
        },
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="collMod should reject hiding a text index by keyPattern as index-not-found",
    ),
]

COLLMOD_INDEX_HIDDEN_TESTS: list[CommandTestCase] = (
    COLLMOD_INDEX_HIDDEN_TRUTHY_TESTS
    + COLLMOD_INDEX_HIDDEN_FALSY_TESTS
    + COLLMOD_INDEX_HIDDEN_UNCHANGED_TESTS
    + COLLMOD_INDEX_ID_HIDDEN_ERROR_TESTS
    + COLLMOD_INDEX_HIDDEN_TYPE_ERROR_TESTS
    + COLLMOD_INDEX_HIDDEN_NULL_ERROR_TESTS
    + COLLMOD_INDEX_HIDDEN_TEXT_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_INDEX_HIDDEN_TESTS))
def test_collMod_index_hidden(database_client, collection, test):
    """Test collMod index hidden acceptance and rejection."""
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
