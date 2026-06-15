"""Tests for aggregate command writeConcern wtimeout sub-field."""

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
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MIN,
)

# Property [writeConcern Sub-field wtimeout Acceptance]: wtimeout accepts
# all types with only an upper-bound numeric constraint.
AGGREGATE_WRITECONCERN_WTIMEOUT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_wtimeout_int_0",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": 0},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept wtimeout=0",
    ),
    CommandTestCase(
        "wc_wtimeout_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": INT32_MAX},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept wtimeout at INT32_MAX",
    ),
    CommandTestCase(
        "wc_wtimeout_negative",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": -1},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept negative wtimeout (no lower bound validation)",
    ),
    CommandTestCase(
        "wc_wtimeout_int32_min",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": INT32_MIN},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept wtimeout at INT32_MIN",
    ),
    CommandTestCase(
        "wc_wtimeout_below_int32_min",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": INT32_UNDERFLOW},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept wtimeout below INT32_MIN",
    ),
    CommandTestCase(
        "wc_wtimeout_int64_min",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": INT64_MIN},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept wtimeout at INT64_MIN",
    ),
    CommandTestCase(
        "wc_wtimeout_double_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": FLOAT_NAN},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept wtimeout NaN (no type error)",
    ),
    CommandTestCase(
        "wc_wtimeout_double_neg_inf",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": FLOAT_NEGATIVE_INFINITY},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept wtimeout -Infinity (no upper bound exceeded)",
    ),
    CommandTestCase(
        "wc_wtimeout_decimal128_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": DECIMAL128_NAN},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept wtimeout Decimal128 NaN",
    ),
    CommandTestCase(
        "wc_wtimeout_decimal128_neg_inf",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": DECIMAL128_NEGATIVE_INFINITY},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept wtimeout Decimal128 -Infinity",
    ),
    *[
        CommandTestCase(
            f"wc_wtimeout_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "writeConcern": {"wtimeout": v},
            },
            expected={"ok": Eq(1.0)},
            msg=f"aggregate should accept wtimeout {tid} (non-numeric types accepted)",
        )
        for tid, val in [
            ("string", "hello"),
            ("bool", True),
            ("null", None),
            ("array", [1, 2]),
            ("document", {"a": 1}),
            ("binary", Binary(b"data")),
            ("regex", Regex(".*")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]

# Property [writeConcern Sub-field wtimeout Rejection]: only numeric values
# exceeding INT32_MAX are rejected.
AGGREGATE_WRITECONCERN_WTIMEOUT_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_wtimeout_reject_int32_overflow",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": INT32_OVERFLOW},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject wtimeout exceeding INT32_MAX",
    ),
    CommandTestCase(
        "wc_wtimeout_reject_double_overflow",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": float(INT32_OVERFLOW)},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject double wtimeout exceeding INT32_MAX",
    ),
    CommandTestCase(
        "wc_wtimeout_reject_decimal128_overflow",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": Decimal128(str(INT32_OVERFLOW))},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject Decimal128 wtimeout exceeding INT32_MAX",
    ),
    CommandTestCase(
        "wc_wtimeout_reject_double_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": FLOAT_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject wtimeout +Infinity (exceeds INT32_MAX)",
    ),
    CommandTestCase(
        "wc_wtimeout_reject_decimal128_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": DECIMAL128_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject wtimeout Decimal128 Infinity (exceeds INT32_MAX)",
    ),
    CommandTestCase(
        "wc_wtimeout_reject_int64_overflow",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"wtimeout": Int64(INT32_OVERFLOW)},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject Int64 wtimeout exceeding INT32_MAX",
    ),
]

AGGREGATE_WRITECONCERN_WTIMEOUT_TESTS = (
    AGGREGATE_WRITECONCERN_WTIMEOUT_ACCEPTANCE_TESTS
    + AGGREGATE_WRITECONCERN_WTIMEOUT_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_WRITECONCERN_WTIMEOUT_TESTS))
def test_aggregate_writeconcern_wtimeout(database_client, collection, test):
    """Test aggregate writeConcern wtimeout sub-field."""
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
