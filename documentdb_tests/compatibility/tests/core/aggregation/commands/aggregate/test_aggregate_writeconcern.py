"""Tests for aggregate command writeConcern parameter."""

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
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [writeConcern Acceptance]: the writeConcern field accepts document
# type and null, and is silently accepted even without $out or $merge.
AGGREGATE_WRITECONCERN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_accept_empty_doc",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept empty writeConcern document",
    ),
    CommandTestCase(
        "wc_accept_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": None,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept null writeConcern",
    ),
    CommandTestCase(
        "wc_accept_without_out_or_merge",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"w": 1},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should silently accept writeConcern without $out or $merge",
    ),
]

# Property [writeConcern Type Rejection]: all non-document, non-null BSON
# types for the writeConcern field produce a type mismatch error.
AGGREGATE_WRITECONCERN_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_type_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"aggregate should reject {tid} writeConcern",
    )
    for tid, val in [
        ("string", "majority"),
        ("int32", 42),
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
]

# Property [writeConcern Other Validation]: writeConcern cross-field
# constraints and unknown sub-fields are validated.
AGGREGATE_WRITECONCERN_OTHER_VALIDATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_other_unknown_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="aggregate should reject unknown field in writeConcern",
    ),
    CommandTestCase(
        "wc_other_unknown_field_uppercase_w",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"W": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="aggregate should reject uppercase W as unknown field (case-sensitive)",
    ),
    CommandTestCase(
        "wc_other_unknown_field_uppercase_wtimeout",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"Wtimeout": 1000},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="aggregate should reject Wtimeout as unknown field (case-sensitive)",
    ),
    CommandTestCase(
        "wc_other_explain_with_out",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": "othercoll"}],
            "explain": True,
            "writeConcern": {"w": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject explain=true with writeConcern even with $out",
    ),
    CommandTestCase(
        "wc_other_explain_with_merge",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$merge": {"into": "othercoll"}}],
            "explain": True,
            "writeConcern": {"w": 1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="aggregate should reject explain=true with writeConcern even with $merge",
    ),
]

AGGREGATE_WRITECONCERN_TESTS = (
    AGGREGATE_WRITECONCERN_ACCEPTANCE_TESTS
    + AGGREGATE_WRITECONCERN_TYPE_REJECTION_TESTS
    + AGGREGATE_WRITECONCERN_OTHER_VALIDATION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_WRITECONCERN_TESTS))
def test_aggregate_writeconcern(database_client, collection, test):
    """Test aggregate writeConcern acceptance and rejection."""
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
