"""Tests for collMod index expireAfterSeconds."""

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
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_OVERFLOW,
    INT64_ZERO,
)

# Property [Index expireAfterSeconds Numeric Coercion]: setting
# index.expireAfterSeconds on an existing TTL index accepts any numeric type and
# coerces it to the new TTL, with a double truncating toward zero and a
# decimal128 using banker's (round-half-to-even) rounding, echoing the prior TTL
# as expireAfterSeconds_old and the coerced value as expireAfterSeconds_new.
COLLMOD_INDEX_EXPIRE_COERCION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"expire_coerce_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_ttl", expireAfterSeconds=100)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_ttl", "expireAfterSeconds": v},
        },
        expected={
            "ok": Eq(1.0),
            "expireAfterSeconds_old": Eq(Int64(100)),
            "expireAfterSeconds_new": Eq(Int64(expected_new)),
        },
        msg=f"collMod should accept a {tid} expireAfterSeconds and coerce it to {expected_new}",
    )
    for tid, val, expected_new in [
        ("int32", 50, 50),
        ("int64", Int64(50), 50),
        ("double_exact", 50.0, 50),
        ("double_truncates_toward_zero", 50.7, 50),
        ("decimal128_rounds_down", Decimal128("50.4"), 50),
        ("decimal128_half_to_even_down", Decimal128("50.5"), 50),
        ("decimal128_rounds_up", Decimal128("50.7"), 51),
        ("decimal128_half_to_even_up", Decimal128("51.5"), 52),
    ]
]

# Property [Index expireAfterSeconds Boundaries]: the lower bound and the upper
# bound are accepted, and a negative value that truncates toward zero to the
# lower bound is accepted.
COLLMOD_INDEX_EXPIRE_BOUNDARY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"expire_boundary_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_ttl", expireAfterSeconds=100)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_ttl", "expireAfterSeconds": v},
        },
        expected={
            "ok": Eq(1.0),
            "expireAfterSeconds_old": Eq(Int64(100)),
            "expireAfterSeconds_new": Eq(Int64(expected_new)),
        },
        msg=f"collMod should accept a {tid} expireAfterSeconds as {expected_new}",
    )
    for tid, val, expected_new in [
        ("zero", 0, 0),
        ("int32_max", INT32_MAX, INT32_MAX),
        ("negative_fraction_truncates_to_zero", -0.9, 0),
    ]
]

# Property [Index expireAfterSeconds Clamp]: a value exceeding int32 max
# (an int64 above int32 max, a double or decimal128 overflow, and positive
# Infinity) is silently clamped to int32 max with no overflow error.
COLLMOD_INDEX_EXPIRE_CLAMP_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"expire_clamp_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_ttl", expireAfterSeconds=100)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_ttl", "expireAfterSeconds": v},
        },
        expected={
            "ok": Eq(1.0),
            "expireAfterSeconds_old": Eq(Int64(100)),
            "expireAfterSeconds_new": Eq(Int64(INT32_MAX)),
        },
        msg=f"collMod should clamp a {tid} expireAfterSeconds to 2147483647",
    )
    for tid, val in [
        ("int64_above_int32_max", Int64(INT32_OVERFLOW)),
        ("double_above_int32_max", float(INT32_OVERFLOW)),
        ("decimal128_overflow", DECIMAL128_INT64_OVERFLOW),
        ("float_infinity", FLOAT_INFINITY),
        ("decimal128_infinity", DECIMAL128_INFINITY),
    ]
]

# Property [Index expireAfterSeconds NaN]: a NaN value (float or decimal128) is
# coerced to 0.
COLLMOD_INDEX_EXPIRE_NAN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"expire_nan_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_ttl", expireAfterSeconds=100)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_ttl", "expireAfterSeconds": v},
        },
        expected={
            "ok": Eq(1.0),
            "expireAfterSeconds_old": Eq(Int64(100)),
            "expireAfterSeconds_new": Eq(INT64_ZERO),
        },
        msg=f"collMod should coerce a {tid} NaN expireAfterSeconds to 0",
    )
    for tid, val in [
        ("float", FLOAT_NAN),
        ("decimal128", DECIMAL128_NAN),
    ]
]

# Property [Index expireAfterSeconds Same Value]: setting expireAfterSeconds to
# the same value on an existing TTL index echoes both expireAfterSeconds_old and
# expireAfterSeconds_new.
COLLMOD_INDEX_EXPIRE_SAME_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expire_same_value",
        indexes=[IndexModel([("a", 1)], name="a_ttl", expireAfterSeconds=100)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_ttl", "expireAfterSeconds": 100},
        },
        expected={
            "ok": Eq(1.0),
            "expireAfterSeconds_old": Eq(Int64(100)),
            "expireAfterSeconds_new": Eq(Int64(100)),
        },
        msg="collMod should echo both old and new TTL when the value is unchanged",
    ),
]

# Property [Index expireAfterSeconds Converts Non-TTL]: setting
# expireAfterSeconds on a single-field non-TTL index converts it to a TTL index,
# echoing expireAfterSeconds_new with no expireAfterSeconds_old.
COLLMOD_INDEX_EXPIRE_CONVERT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expire_converts_non_ttl",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "expireAfterSeconds": 50},
        },
        expected={
            "ok": Eq(1.0),
            "expireAfterSeconds_old": NotExists(),
            "expireAfterSeconds_new": Eq(Int64(50)),
        },
        msg="collMod should convert a non-TTL index to TTL with new value and no old value",
    ),
]

# Property [Index Field Combination expireAfterSeconds And hidden]: setting
# expireAfterSeconds and hidden in one index document applies both, echoing the
# new TTL as expireAfterSeconds_new and the hidden change as hidden_old and
# hidden_new.
COLLMOD_INDEX_COMBO_EXPIRE_HIDDEN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "combo_expire_and_hidden",
        indexes=[IndexModel([("a", 1)], name="a_ttl", expireAfterSeconds=100, hidden=False)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_ttl", "expireAfterSeconds": 200, "hidden": True},
        },
        expected={
            "ok": Eq(1.0),
            "expireAfterSeconds_old": Eq(Int64(100)),
            "expireAfterSeconds_new": Eq(Int64(200)),
            "hidden_old": Eq(False),
            "hidden_new": Eq(True),
        },
        msg="collMod should apply both expireAfterSeconds and hidden in one index document",
    ),
]

# Property [Index expireAfterSeconds Non-Numeric Rejection]: a bool value and
# every other non-numeric type for index.expireAfterSeconds produce a
# type-mismatch error (bool is not treated as numeric here).
COLLMOD_INDEX_EXPIRE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"expire_type_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_ttl", expireAfterSeconds=100)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_ttl", "expireAfterSeconds": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} expireAfterSeconds as a type mismatch",
    )
    for tid, val in [
        ("string", "100"),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [100]),
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

# Property [Index expireAfterSeconds Null Rejection]: a null
# index.expireAfterSeconds leaves no modification field and is rejected as an
# invalid option.
COLLMOD_INDEX_EXPIRE_NULL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expire_null",
        indexes=[IndexModel([("a", 1)], name="a_ttl", expireAfterSeconds=100)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_ttl", "expireAfterSeconds": None},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject a null expireAfterSeconds as leaving no modification field",
    ),
]

# Property [Index expireAfterSeconds Negative Rejection]: a value that truncates
# toward zero to a negative number is rejected as an invalid option, including
# -Infinity, which is rejected as below zero rather than clamped like +Infinity.
COLLMOD_INDEX_EXPIRE_NEGATIVE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"expire_negative_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_ttl", expireAfterSeconds=100)],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "index": {"name": "a_ttl", "expireAfterSeconds": v},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"collMod should reject a {tid} expireAfterSeconds that truncates to a negative value",
    )
    for tid, val in [
        ("int32", -1),
        ("int64", Int64(-1)),
        ("double", -1.5),
        ("decimal128", Decimal128("-1")),
        ("float_negative_infinity", FLOAT_NEGATIVE_INFINITY),
        ("decimal128_negative_infinity", DECIMAL128_NEGATIVE_INFINITY),
    ]
]

# Property [Index expireAfterSeconds Converts Special Single-Field Index Types]:
# setting expireAfterSeconds on a single-field hashed or geospatial (2dsphere)
# index converts it to a TTL index, echoing expireAfterSeconds_new with no
# expireAfterSeconds_old, because TTL eligibility is decided by the key shape
# (single-field non-_id), not the index sub-type.
COLLMOD_INDEX_EXPIRE_SPECIAL_TYPE_CONVERT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"expire_converts_{tid}",
        indexes=[IndexModel(key, name=name)],
        docs=[],
        command=lambda ctx, n=name: {
            "collMod": ctx.collection,
            "index": {"name": n, "expireAfterSeconds": 100},
        },
        expected={
            "ok": Eq(1.0),
            "expireAfterSeconds_old": NotExists(),
            "expireAfterSeconds_new": Eq(Int64(100)),
        },
        msg=f"collMod should convert a single-field {tid} index to TTL with a new value "
        "and no old value",
    )
    for tid, key, name in [
        ("hashed", [("a", "hashed")], "a_hashed"),
        ("2dsphere", [("loc", "2dsphere")], "loc_2dsphere"),
    ]
]

# Property [Index expireAfterSeconds Non-Single-Field Rejection]: applying
# expireAfterSeconds to certain index types is rejected as an invalid option,
# since TTL is supported only on single-field non-_id indexes.
COLLMOD_INDEX_EXPIRE_NON_SINGLE_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expire_compound_index",
        indexes=[IndexModel([("a", 1), ("b", 1)], name="ab_1")],
        docs=[{"_id": 1, "a": 1, "b": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "ab_1", "expireAfterSeconds": 100},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject expireAfterSeconds on a compound index as an invalid option",
    ),
    CommandTestCase(
        "expire_id_index",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "_id_", "expireAfterSeconds": 100},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject expireAfterSeconds on the _id_ index as an invalid option",
    ),
    CommandTestCase(
        "expire_text_index",
        indexes=[IndexModel([("a", "text")], name="a_text")],
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_text", "expireAfterSeconds": 100},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject expireAfterSeconds on a text index as an invalid option",
    ),
]

# Property [Index expireAfterSeconds Wildcard Crash]: applying expireAfterSeconds
# to a wildcard index must not crash the engine and must return a clean
# InvalidOptions error, since a wildcard index is not a valid TTL target.
COLLMOD_INDEX_EXPIRE_WILDCARD_CRASH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expire_wildcard_index",
        indexes=[IndexModel([("$**", 1)], name="wild")],
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "wild", "expireAfterSeconds": 100},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject expireAfterSeconds on a wildcard index with a clean error "
        "and not crash",
        marks=(
            pytest.mark.engine_xcrash(
                engine="mongodb",
                reason="Server crashes when expireAfterSeconds is applied to a wildcard index",
            ),
        ),
    ),
]

COLLMOD_INDEX_EXPIRE_TESTS: list[CommandTestCase] = (
    COLLMOD_INDEX_EXPIRE_COERCION_TESTS
    + COLLMOD_INDEX_EXPIRE_BOUNDARY_TESTS
    + COLLMOD_INDEX_EXPIRE_CLAMP_TESTS
    + COLLMOD_INDEX_EXPIRE_NAN_TESTS
    + COLLMOD_INDEX_EXPIRE_SAME_VALUE_TESTS
    + COLLMOD_INDEX_EXPIRE_CONVERT_TESTS
    + COLLMOD_INDEX_EXPIRE_SPECIAL_TYPE_CONVERT_TESTS
    + COLLMOD_INDEX_COMBO_EXPIRE_HIDDEN_TESTS
    + COLLMOD_INDEX_EXPIRE_TYPE_ERROR_TESTS
    + COLLMOD_INDEX_EXPIRE_NULL_ERROR_TESTS
    + COLLMOD_INDEX_EXPIRE_NEGATIVE_ERROR_TESTS
    + COLLMOD_INDEX_EXPIRE_NON_SINGLE_FIELD_ERROR_TESTS
    + COLLMOD_INDEX_EXPIRE_WILDCARD_CRASH_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_INDEX_EXPIRE_TESTS))
def test_collMod_index_expire(database_client, collection, test):
    """Test collMod index expireAfterSeconds acceptance and rejection."""
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
