"""Tests for aggregate command maxTimeMS parameter."""

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
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists
from documentdb_tests.framework.target_collection import ViewCollection
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_OVERFLOW,
    INT64_MAX,
    INT64_ZERO,
)

# Property [maxTimeMS Acceptance]: valid maxTimeMS values are accepted
# across all aggregate modes.
AGGREGATE_MAXTIMEMS_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "maxtimems_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": 5000,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept int32 maxTimeMS",
    ),
    CommandTestCase(
        "maxtimems_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": Int64(5000),
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Int64 maxTimeMS",
    ),
    CommandTestCase(
        "maxtimems_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": 5000.0,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept double maxTimeMS",
    ),
    CommandTestCase(
        "maxtimems_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": Decimal128("5000"),
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 maxTimeMS",
    ),
    CommandTestCase(
        "maxtimems_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": INT32_MAX,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept INT32_MAX as the upper bound of maxTimeMS",
    ),
    CommandTestCase(
        "maxtimems_zero_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": 0,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept int32 0 maxTimeMS as unbounded",
    ),
    CommandTestCase(
        "maxtimems_zero_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": INT64_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Int64 0 maxTimeMS as unbounded",
    ),
    CommandTestCase(
        "maxtimems_zero_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": DOUBLE_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept double 0.0 maxTimeMS as unbounded",
    ),
    CommandTestCase(
        "maxtimems_zero_neg_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": DOUBLE_NEGATIVE_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept -0.0 maxTimeMS as unbounded",
    ),
    CommandTestCase(
        "maxtimems_zero_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": DECIMAL128_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128('0') maxTimeMS as unbounded",
    ),
    CommandTestCase(
        "maxtimems_zero_neg_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128('-0') maxTimeMS as unbounded",
    ),
    CommandTestCase(
        "maxtimems_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": None,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept null maxTimeMS as unbounded",
    ),
    CommandTestCase(
        "maxtimems_decimal128_trailing_zeros",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": Decimal128("5000.0"),
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 with trailing zeros resolving to whole number",
    ),
    CommandTestCase(
        "maxtimems_decimal128_trailing_zeros_2",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": Decimal128("100.00"),
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 with multiple trailing zeros",
    ),
    CommandTestCase(
        "maxtimems_decimal128_scientific",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": Decimal128("50E2"),
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 in scientific notation resolving to whole number",
    ),
    CommandTestCase(
        "maxtimems_decimal128_neg_exponent",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": Decimal128("50000E-1"),
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 with negative exponent resolving to whole number",
    ),
    CommandTestCase(
        "maxtimems_nonexistent_collection",
        docs=None,
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": 5000,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept maxTimeMS on a non-existent collection",
    ),
    CommandTestCase(
        "maxtimems_view",
        target_collection=ViewCollection(),
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "maxTimeMS": 5000,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept maxTimeMS on a view",
    ),
    CommandTestCase(
        "maxtimems_explain",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "explain": True,
            "maxTimeMS": 5000,
        },
        expected={"ok": Eq(1.0), "queryPlanner": Exists()},
        msg="aggregate should accept maxTimeMS with explain mode",
    ),
    CommandTestCase(
        "maxtimems_agnostic",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"x": 1}]}],
            "cursor": {},
            "maxTimeMS": 5000,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept maxTimeMS in collection-agnostic mode",
    ),
]

# Property [maxTimeMS Rejection]: invalid types and out-of-range values for
# maxTimeMS are rejected.
AGGREGATE_MAXTIMEMS_REJECTION_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"maxtimems_reject_{tid}",
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "maxTimeMS": v,
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"aggregate should reject {tid} maxTimeMS",
        )
        for tid, val in [
            ("string", "5000"),
            ("bool", True),
            ("array", [5000]),
            ("document", {"x": 1}),
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
    *[
        CommandTestCase(
            f"maxtimems_reject_{tid}",
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "maxTimeMS": v,
            },
            error_code=FAILED_TO_PARSE_ERROR,
            msg=f"aggregate should reject {tid} maxTimeMS",
        )
        for tid, val in [
            ("fractional_double", 1.5),
            ("fractional_decimal128", DECIMAL128_ONE_AND_HALF),
            ("nan_double", FLOAT_NAN),
            ("nan_decimal128", DECIMAL128_NAN),
            ("infinity_double", FLOAT_INFINITY),
            ("neg_infinity_double", FLOAT_NEGATIVE_INFINITY),
            ("infinity_decimal128", DECIMAL128_INFINITY),
            ("neg_infinity_decimal128", DECIMAL128_NEGATIVE_INFINITY),
        ]
    ],
    *[
        CommandTestCase(
            f"maxtimems_reject_{tid}",
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "maxTimeMS": v,
            },
            error_code=BAD_VALUE_ERROR,
            msg=f"aggregate should reject {tid} maxTimeMS",
        )
        for tid, val in [
            ("negative_int32", -1),
            ("negative_int64", Int64(-100)),
            ("negative_double", -1.0),
            ("negative_decimal128", Decimal128("-1")),
            ("exceeds_int32_max", INT32_OVERFLOW),
            ("exceeds_int32_max_int64", INT64_MAX),
            ("exceeds_int32_max_decimal128", Decimal128(str(INT32_OVERFLOW))),
        ]
    ],
]

AGGREGATE_MAXTIMEMS_TESTS = (
    AGGREGATE_MAXTIMEMS_ACCEPTANCE_TESTS + AGGREGATE_MAXTIMEMS_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_MAXTIMEMS_TESTS))
def test_aggregate_maxtimems(database_client, collection, test):
    """Test aggregate maxTimeMS acceptance and rejection."""
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
