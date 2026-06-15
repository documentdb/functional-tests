"""Tests for collMod cappedMax and cappedSize/cappedMax coexistence on capped collections."""

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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
    ExistingDatabase,
    ViewCollection,
)
from documentdb_tests.framework.test_constants import (
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_OVERFLOW,
)

# Property [cappedMax Numeric Type Acceptance]: cappedMax accepts any numeric type.
COLLMOD_CAPPED_MAX_NUMERIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_numeric_int32",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": 1_000},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an int32 cappedMax",
    ),
    CommandTestCase(
        "max_numeric_int64",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": Int64(1_000)},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an int64 cappedMax",
    ),
    CommandTestCase(
        "max_numeric_double",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": 1_000.0},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a double cappedMax",
    ),
    CommandTestCase(
        "max_numeric_decimal",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": Decimal128("1000")},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a decimal128 cappedMax",
    ),
]

# Property [cappedMax Null No-Op]: a null cappedMax is accepted as a no-op.
COLLMOD_CAPPED_MAX_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_null",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": None},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a null cappedMax as a no-op",
    ),
]

# Property [cappedMax No Lower Bound]: any value at or below 0, NaN, or
# -Infinity is accepted and means "no document limit"; cappedMax has no lower
# bound, unlike cappedSize.
COLLMOD_CAPPED_MAX_NO_LOWER_BOUND_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_zero",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": 0},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a cappedMax of 0 as no document limit",
    ),
    CommandTestCase(
        "max_negative",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": -1},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a negative cappedMax as no document limit",
    ),
    CommandTestCase(
        "max_nan",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": FLOAT_NAN},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a NaN cappedMax as no document limit",
    ),
    CommandTestCase(
        "max_negative_infinity",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": FLOAT_NEGATIVE_INFINITY},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a -Infinity cappedMax as no document limit",
    ),
]

# Property [cappedMax Upper Boundary]: the boundary value INT32_MAX is accepted.
COLLMOD_CAPPED_MAX_BOUNDARY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_upper_boundary_int32_max",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": INT32_MAX},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept the upper boundary cappedMax of INT32_MAX",
    ),
]

# Property [cappedMax Fractional Coercion]: a fractional cappedMax is coerced to
# an integer before the range check, with a double truncating toward zero and a
# decimal128 using banker's (round-half-to-even) rounding; a value that lands
# below the exclusive upper bound is accepted.
COLLMOD_CAPPED_MAX_FRACTIONAL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_double_truncates_toward_zero",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": INT32_MAX + 0.5},
        expected={"ok": Eq(1.0)},
        msg="collMod should truncate a fractional double cappedMax toward zero to INT32_MAX, "
        "below the exclusive upper bound",
    ),
    CommandTestCase(
        "max_decimal_bankers_rounds_down",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": Decimal128(f"{INT32_MAX}.4")},
        expected={"ok": Eq(1.0)},
        msg="collMod should banker's-round a fractional decimal128 cappedMax down to INT32_MAX, "
        "below the exclusive upper bound",
    ),
]

# Property [cappedMax Type Rejection]: any non-numeric cappedMax type produces a
# TypeMismatch error.
COLLMOD_CAPPED_MAX_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"max_type_reject_{tid}",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "cappedMax": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} cappedMax as a non-numeric type",
    )
    for tid, val in [
        ("string", "1000"),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [1000]),
        ("object", {"x": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"hello")),
        ("regex", Regex("abc", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [cappedMax Strict Upper Bound]: a value at or above the upper bound
# produces a BadValue error, since the bound is exclusive unlike cappedSize's
# inclusive bound, including a decimal128 that banker's-rounds up onto the bound
# and +Infinity which coerces above the bound.
COLLMOD_CAPPED_MAX_HIGH_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_high_at_bound",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": INT32_OVERFLOW},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a cappedMax of 2^31 as at or above the strict upper bound",
    ),
    CommandTestCase(
        "max_high_decimal_bankers_rounds_onto_bound",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": Decimal128(f"{INT32_MAX}.5")},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a decimal128 cappedMax that banker's-rounds half-to-even up "
        "onto the strict upper bound",
    ),
    CommandTestCase(
        "max_high_positive_infinity",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": FLOAT_INFINITY},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a +Infinity cappedMax, which coerces to INT64_MAX, "
        "as above the upper bound",
    ),
]

# Property [cappedMax Target Collection Restrictions]: cappedMax is rejected on
# any non-capped target: a regular or clustered collection produces an
# InvalidOptions error, a non-existent collection produces a NamespaceNotFound
# error, and the oplog produces an InvalidOptions error.
COLLMOD_CAPPED_MAX_TARGET_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_target_regular",
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": 1_000},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject cappedMax on a regular collection",
    ),
    CommandTestCase(
        "max_target_clustered",
        target_collection=ClusteredCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": 1_000},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject cappedMax on a clustered collection",
    ),
    CommandTestCase(
        "max_target_nonexistent",
        docs=None,
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": 1_000},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="collMod should reject cappedMax on a non-existent collection",
    ),
    CommandTestCase(
        "max_target_oplog",
        target_collection=ExistingDatabase(db_name="local"),
        docs=None,
        command=lambda ctx: {"collMod": "oplog.rs", "cappedMax": 1_000},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject cappedMax on the oplog",
        marks=(pytest.mark.replica_set,),
    ),
]

# Property [cappedMax View Crash]: applying cappedMax to a view must not crash
# the engine and must return a clean InvalidOptions error; the reference engine
# is skipped because it crashes (SIGSEGV) on this input.
COLLMOD_CAPPED_MAX_VIEW_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "max_target_view",
        target_collection=ViewCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedMax": 1_000},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject cappedMax on a view with a clean error and not crash",
        marks=(
            pytest.mark.engine_xcrash(
                engine="mongodb",
                reason="Server crashes (SIGSEGV) when cappedMax is applied to a view",
            ),
        ),
    ),
]

# Property [cappedSize And cappedMax Coexistence]: cappedSize and cappedMax, the
# two capped-group sub-options, apply together in one command on a capped
# collection, each taking effect independently.
COLLMOD_CAPPED_SIZE_AND_MAX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "size_and_max_together",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "cappedSize": 16384,
            "cappedMax": 99,
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should apply cappedSize and cappedMax together in one command",
    ),
]

COLLMOD_CAPPED_MAX_TESTS: list[CommandTestCase] = (
    COLLMOD_CAPPED_MAX_NUMERIC_TESTS
    + COLLMOD_CAPPED_MAX_NULL_TESTS
    + COLLMOD_CAPPED_MAX_NO_LOWER_BOUND_TESTS
    + COLLMOD_CAPPED_MAX_BOUNDARY_TESTS
    + COLLMOD_CAPPED_MAX_FRACTIONAL_TESTS
    + COLLMOD_CAPPED_MAX_TYPE_ERROR_TESTS
    + COLLMOD_CAPPED_MAX_HIGH_ERROR_TESTS
    + COLLMOD_CAPPED_MAX_TARGET_ERROR_TESTS
    + COLLMOD_CAPPED_MAX_VIEW_ERROR_TESTS
    + COLLMOD_CAPPED_SIZE_AND_MAX_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_CAPPED_MAX_TESTS))
def test_collMod_capped_max(database_client, collection, test):
    """Test collMod cappedMax acceptance, rejection, and coexistence with cappedSize."""
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
