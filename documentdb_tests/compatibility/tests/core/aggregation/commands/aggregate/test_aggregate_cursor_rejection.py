"""Tests for aggregate command cursor field rejection."""

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

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Cursor Rejection]: invalid cursor field types, sub-fields, and
# batchSize values are rejected.
AGGREGATE_CURSOR_REJECTION_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"cursor_reject_{tid}",
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": v,
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"aggregate should reject {tid} cursor",
        )
        for tid, val in [
            ("null", None),
            ("string", "hello"),
            ("int", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1, 2]),
            ("binary", Binary(b"data")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("regex", Regex(".*")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        "cursor_reject_negative_batchsize_int",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": -1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative int32 batchSize",
    ),
    CommandTestCase(
        "cursor_reject_negative_batchsize_int64",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": Int64(-10)},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative Int64 batchSize",
    ),
    CommandTestCase(
        "cursor_reject_negative_batchsize_double",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": -1.0},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative double batchSize",
    ),
    CommandTestCase(
        "cursor_reject_negative_batchsize_decimal128",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": Decimal128("-5")},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative Decimal128 batchSize",
    ),
    CommandTestCase(
        "cursor_reject_decimal128_bankers_neg",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": Decimal128("-0.9")},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject Decimal128('-0.9') that rounds to -1 via banker's rounding",
    ),
    CommandTestCase(
        "cursor_reject_negative_infinity_double",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": FLOAT_NEGATIVE_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative infinity double batchSize",
    ),
    CommandTestCase(
        "cursor_reject_negative_infinity_decimal128",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": DECIMAL128_NEGATIVE_INFINITY},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject Decimal128 negative infinity batchSize",
    ),
    CommandTestCase(
        "cursor_reject_unknown_subfield",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="aggregate should reject unknown sub-fields in cursor document",
    ),
    CommandTestCase(
        "cursor_reject_wrong_case_subfield",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"BatchSize": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="aggregate should reject wrong-case sub-field name in cursor document",
    ),
    *[
        CommandTestCase(
            f"cursor_reject_batchsize_{tid}",
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {"batchSize": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"aggregate should reject {tid} batchSize",
        )
        for tid, val in [
            ("string", "hello"),
            ("bool", True),
            ("array", [1]),
            ("document", {"x": 1}),
            ("binary", Binary(b"x")),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("regex", Regex(".*")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]

# Property [Cursor Requirement]: the cursor field is required unless
# explain=true is specified.
AGGREGATE_CURSOR_REQUIREMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursor_required_no_explain",
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": []},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should require cursor field when explain is not specified",
    ),
    CommandTestCase(
        "cursor_required_explain_false",
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "explain": False},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should require cursor field when explain=false",
    ),
    CommandTestCase(
        "cursor_type_enforced_with_explain_true",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": 123,
            "explain": True,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject non-document cursor type even when explain=true",
    ),
    CommandTestCase(
        "cursor_unknown_field_with_explain_true",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"unknownField": 1},
            "explain": True,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="aggregate should reject unknown cursor sub-fields even when explain=true",
    ),
    CommandTestCase(
        "cursor_negative_batchsize_with_explain_true",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": -5},
            "explain": True,
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative batchSize even when explain=true",
    ),
]

AGGREGATE_CURSOR_TESTS = AGGREGATE_CURSOR_REJECTION_TESTS + AGGREGATE_CURSOR_REQUIREMENT_TESTS


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_CURSOR_TESTS))
def test_aggregate_cursor_rejection(database_client, collection, test):
    """Test aggregate cursor field rejection."""
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
