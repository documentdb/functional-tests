"""Tests for collMod cappedSize on capped collections."""

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
    CAPPED_SIZE_LIMIT_BYTES,
    DECIMAL128_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [cappedSize Numeric Type Acceptance]: cappedSize accepts any numeric type.
COLLMOD_CAPPED_SIZE_NUMERIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "size_numeric_int32",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": 100_000},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an int32 cappedSize",
    ),
    CommandTestCase(
        "size_numeric_int64",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": Int64(100_000)},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an int64 cappedSize",
    ),
    CommandTestCase(
        "size_numeric_double",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": 100_000.0},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a double cappedSize",
    ),
    CommandTestCase(
        "size_numeric_decimal",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": Decimal128("100000")},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a decimal128 cappedSize",
    ),
]

# Property [cappedSize Null No-Op]: a null cappedSize is accepted as a no-op.
COLLMOD_CAPPED_SIZE_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "size_null",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": None},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a null cappedSize as a no-op",
    ),
]

# Property [cappedSize Range Boundaries]: the inclusive lower and upper
# boundaries are both accepted.
COLLMOD_CAPPED_SIZE_BOUNDARY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "size_lower_boundary_1",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": 1},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept the lower boundary cappedSize of 1",
    ),
    CommandTestCase(
        "size_upper_boundary_max",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": CAPPED_SIZE_LIMIT_BYTES},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept the upper boundary cappedSize of 2^50",
    ),
]

# Property [cappedSize Fractional Coercion]: a fractional cappedSize is coerced
# to an integer before the range check, with a double truncating toward zero and
# a decimal128 using banker's (round-half-to-even) rounding; a value that lands
# at or above the lower boundary is accepted.
COLLMOD_CAPPED_SIZE_FRACTIONAL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "size_double_truncates_to_one",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": 1.5},
        expected={"ok": Eq(1.0)},
        msg="collMod should truncate a fractional double cappedSize toward zero to the "
        "lower boundary",
    ),
    CommandTestCase(
        "size_decimal_bankers_rounds_up_to_one",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": Decimal128("0.7")},
        expected={"ok": Eq(1.0)},
        msg="collMod should banker's-round a fractional decimal128 cappedSize up to the "
        "lower boundary",
    ),
]

# Property [cappedSize Type Rejection]: any non-numeric cappedSize type produces
# a TypeMismatch error.
COLLMOD_CAPPED_SIZE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"size_type_reject_{tid}",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "cappedSize": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} cappedSize as a non-numeric type",
    )
    for tid, val in [
        ("string", "8192"),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [8192]),
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

# Property [cappedSize Below Lower Bound]: a value below the inclusive lower
# bound after coercion produces a BadValue error, whether a double truncates
# toward zero or a decimal128 banker's-rounds down to zero.
COLLMOD_CAPPED_SIZE_LOW_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "size_low_zero",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": 0},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a cappedSize of 0 as below the lower bound",
    ),
    CommandTestCase(
        "size_low_double_truncates_to_zero",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": 0.7},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a double cappedSize that truncates toward zero to 0 "
        "as below the lower bound",
    ),
    CommandTestCase(
        "size_low_decimal_bankers_rounds_to_zero",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": DECIMAL128_HALF},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a decimal128 cappedSize that banker's-rounds half-to-even "
        "to 0 as below the lower bound",
    ),
    CommandTestCase(
        "size_low_negative_fraction_truncates_to_zero",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": -0.5},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a negative fractional cappedSize that truncates toward zero "
        "to 0 as below the lower bound",
    ),
    CommandTestCase(
        "size_low_nan",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": FLOAT_NAN},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a NaN cappedSize, which coerces to 0, as below the lower bound",
    ),
    CommandTestCase(
        "size_low_negative_infinity",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": FLOAT_NEGATIVE_INFINITY},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a -Infinity cappedSize, which coerces to INT64_MIN, "
        "as below the lower bound",
    ),
]

# Property [cappedSize Above Upper Bound]: a value above the inclusive upper
# bound produces a BadValue error, including a decimal128 that banker's-rounds up
# over the bound and +Infinity which coerces above the bound.
COLLMOD_CAPPED_SIZE_HIGH_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "size_high_above_max",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": CAPPED_SIZE_LIMIT_BYTES + 1},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a cappedSize just above the 2^50 upper bound",
    ),
    CommandTestCase(
        "size_high_decimal_bankers_rounds_over_bound",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "cappedSize": Decimal128(f"{CAPPED_SIZE_LIMIT_BYTES}.7"),
        },
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a decimal128 cappedSize that banker's-rounds up over the "
        "upper bound",
    ),
    CommandTestCase(
        "size_high_positive_infinity",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": FLOAT_INFINITY},
        error_code=BAD_VALUE_ERROR,
        msg="collMod should reject a +Infinity cappedSize, which coerces to INT64_MAX, "
        "as above the upper bound",
    ),
]

# Property [cappedSize Target Collection Restrictions]: cappedSize is rejected on
# any non-capped target: a regular or clustered collection produces an
# InvalidOptions error, a non-existent collection produces a NamespaceNotFound
# error, and the oplog produces an InvalidOptions error.
COLLMOD_CAPPED_SIZE_TARGET_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "size_target_regular",
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": 100_000},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject cappedSize on a regular collection",
    ),
    CommandTestCase(
        "size_target_clustered",
        target_collection=ClusteredCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": 100_000},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject cappedSize on a clustered collection",
    ),
    CommandTestCase(
        "size_target_nonexistent",
        docs=None,
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": 100_000},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="collMod should reject cappedSize on a non-existent collection",
    ),
    CommandTestCase(
        "size_target_oplog",
        target_collection=ExistingDatabase(db_name="local"),
        docs=None,
        command=lambda ctx: {"collMod": "oplog.rs", "cappedSize": 100_000},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject cappedSize on the oplog",
        marks=(pytest.mark.replica_set,),
    ),
]

# Property [cappedSize View Crash]: applying cappedSize to a view must not crash
# the engine and must return a clean InvalidOptions error; the reference engine
# is skipped because it crashes (SIGSEGV) on this input.
COLLMOD_CAPPED_SIZE_VIEW_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "size_target_view",
        target_collection=ViewCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection, "cappedSize": 100_000},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject cappedSize on a view with a clean error and not crash",
        marks=(
            pytest.mark.engine_xcrash(
                engine="mongodb",
                reason="Server crashes (SIGSEGV) when cappedSize is applied to a view",
            ),
        ),
    ),
]

COLLMOD_CAPPED_SIZE_TESTS: list[CommandTestCase] = (
    COLLMOD_CAPPED_SIZE_NUMERIC_TESTS
    + COLLMOD_CAPPED_SIZE_NULL_TESTS
    + COLLMOD_CAPPED_SIZE_BOUNDARY_TESTS
    + COLLMOD_CAPPED_SIZE_FRACTIONAL_TESTS
    + COLLMOD_CAPPED_SIZE_TYPE_ERROR_TESTS
    + COLLMOD_CAPPED_SIZE_LOW_ERROR_TESTS
    + COLLMOD_CAPPED_SIZE_HIGH_ERROR_TESTS
    + COLLMOD_CAPPED_SIZE_TARGET_ERROR_TESTS
    + COLLMOD_CAPPED_SIZE_VIEW_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_CAPPED_SIZE_TESTS))
def test_collMod_capped_size(database_client, collection, test):
    """Test collMod cappedSize acceptance and rejection on capped collections."""
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
