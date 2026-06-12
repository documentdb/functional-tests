"""Tests for aggregate command writeConcern w sub-field."""

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
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
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
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [writeConcern Sub-field w Acceptance]: valid w values are
# accepted with type-specific numeric coercion.
AGGREGATE_WRITECONCERN_W_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_w_int32_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": 0},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept w=0 as int32",
    ),
    CommandTestCase(
        "wc_w_int32_fifty",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": 50},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should accept w=50 as in-range; standalone rejects w>1 not as out-of-range",
    ),
    CommandTestCase(
        "wc_w_int64_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": INT64_ZERO},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept w=0 as Int64",
    ),
    CommandTestCase(
        "wc_w_int64_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": Int64(1)},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept w=1 as Int64",
    ),
    CommandTestCase(
        "wc_w_double_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": DOUBLE_ZERO},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept w=0.0 as double",
    ),
    CommandTestCase(
        "wc_w_double_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": 1.0},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept w=1.0 as double",
    ),
    CommandTestCase(
        "wc_w_double_truncate_0_9",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": 0.9},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should truncate double w=0.9 toward zero to 0",
    ),
    CommandTestCase(
        "wc_w_double_truncate_1_9",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": 1.9},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should truncate double w=1.9 toward zero to 1",
    ),
    CommandTestCase(
        "wc_w_double_truncate_1_5",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": 1.5},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should truncate double w=1.5 toward zero to 1",
    ),
    CommandTestCase(
        "wc_w_decimal128_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": DECIMAL128_ZERO},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept w=Decimal128('0')",
    ),
    CommandTestCase(
        "wc_w_decimal128_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": Decimal128("1")},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept w=Decimal128('1')",
    ),
    CommandTestCase(
        "wc_w_double_truncate_50_99",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": 50.99},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should truncate w=50.99 to 50; standalone rejects w>1 not as out-of-range",
    ),
    CommandTestCase(
        "wc_w_decimal128_bankers_0_5",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": DECIMAL128_HALF},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should round Decimal128 w=0.5 to 0 via banker's rounding",
    ),
    CommandTestCase(
        "wc_w_decimal128_bankers_1_5",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": DECIMAL128_ONE_AND_HALF},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should round Decimal128 w=1.5 to 2; standalone rejects w>1 not out-of-range",
    ),
    CommandTestCase(
        "wc_w_decimal128_bankers_50_5",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": Decimal128("50.5")},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should round Decimal128 w=50.5 to 50; standalone rejects not out-of-range",
    ),
    CommandTestCase(
        "wc_w_string_majority",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": "majority"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept w='majority' on standalone",
    ),
    CommandTestCase(
        "wc_w_object_tag_set",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": {"dc1": 1}},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept w as an object (tag set)",
    ),
]

# Property [writeConcern Sub-field w Rejection]: invalid types and
# out-of-range values for w are rejected.
AGGREGATE_WRITECONCERN_W_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_w_reject_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": True},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject boolean w",
    ),
    CommandTestCase(
        "wc_w_reject_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": [1]},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject array w",
    ),
    CommandTestCase(
        "wc_w_reject_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": None},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject null w coerced to empty string",
    ),
    CommandTestCase(
        "wc_w_reject_negative",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": -1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject negative w",
    ),
    CommandTestCase(
        "wc_w_reject_over_50",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": 51},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject w greater than 50",
    ),
    CommandTestCase(
        "wc_w_reject_gt1_standalone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": 2},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject w>1 on standalone",
    ),
    *[
        CommandTestCase(
            f"wc_w_reject_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "writeConcern": {"w": v},
            },
            error_code=FAILED_TO_PARSE_ERROR,
            msg=f"aggregate should reject {tid} w",
        )
        for tid, val in [
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"data")),
            ("regex", Regex(".*")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
            ("nan_double", FLOAT_NAN),
            ("nan_decimal128", DECIMAL128_NAN),
            ("infinity_double", FLOAT_INFINITY),
            ("neg_infinity_double", FLOAT_NEGATIVE_INFINITY),
            ("infinity_decimal128", DECIMAL128_INFINITY),
            ("neg_infinity_decimal128", DECIMAL128_NEGATIVE_INFINITY),
        ]
    ],
]

# Property [writeConcern Sub-field w Tagged Rejection]: tagged write concern
# objects must be non-empty with only numeric values.
AGGREGATE_WRITECONCERN_W_TAGGED_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_w_tagged_reject_empty",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": {}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject empty object w (tagged requires tags)",
    ),
    CommandTestCase(
        "wc_w_tagged_reject_string_value",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": {"dc1": "hello"}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject non-numeric tag value",
    ),
    CommandTestCase(
        "wc_w_tagged_reject_nested_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": {"dc1": {"nested": 1}}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject nested object in tag value",
    ),
]

# Property [writeConcern Sub-field w Numeric Boundaries]: extreme numeric
# values for w produce appropriate errors.
AGGREGATE_WRITECONCERN_W_NUMERIC_BOUNDARY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_w_boundary_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": INT32_MAX},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject w at INT32_MAX (exceeds 50)",
    ),
    CommandTestCase(
        "wc_w_boundary_int64_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": INT64_MAX},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject w at INT64_MAX",
    ),
    CommandTestCase(
        "wc_w_boundary_int64_min",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": INT64_MIN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject w at INT64_MIN",
    ),
]

# Property [writeConcern Sub-field w Negative Zero]: negative zero in
# double and Decimal128 is coerced to 0 and accepted.
AGGREGATE_WRITECONCERN_W_NEGATIVE_ZERO_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_w_double_negative_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": DOUBLE_NEGATIVE_ZERO},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept w=-0.0 (double negative zero coerced to 0)",
    ),
    CommandTestCase(
        "wc_w_decimal128_negative_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": DECIMAL128_NEGATIVE_ZERO},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept w=Decimal128('-0') (coerced to 0)",
    ),
]

# Property [writeConcern Sub-field w Coercion Boundary]: Decimal128
# rounding can push a value across the >50 rejection boundary.
AGGREGATE_WRITECONCERN_W_COERCION_BOUNDARY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_w_decimal128_rounds_to_51",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": Decimal128("51.4")},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject Decimal128 w=51.4 (rounds to 51, exceeds 50)",
    ),
]

AGGREGATE_WRITECONCERN_W_TESTS = (
    AGGREGATE_WRITECONCERN_W_ACCEPTANCE_TESTS
    + AGGREGATE_WRITECONCERN_W_REJECTION_TESTS
    + AGGREGATE_WRITECONCERN_W_TAGGED_REJECTION_TESTS
    + AGGREGATE_WRITECONCERN_W_NUMERIC_BOUNDARY_TESTS
    + AGGREGATE_WRITECONCERN_W_NEGATIVE_ZERO_TESTS
    + AGGREGATE_WRITECONCERN_W_COERCION_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_WRITECONCERN_W_TESTS))
def test_aggregate_writeconcern_w(database_client, collection, test):
    """Test aggregate writeConcern w sub-field."""
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
