"""Tests for aggregate command readConcern parameter."""

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
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [readConcern Acceptance]: valid readConcern values are accepted
# and produce default or level-specific behavior.
AGGREGATE_READCONCERN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": None,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept null readConcern",
    ),
    CommandTestCase(
        "readconcern_empty_doc",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept empty document readConcern as default",
    ),
    CommandTestCase(
        "readconcern_level_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": None},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern with level null as default",
    ),
    CommandTestCase(
        "readconcern_omitted",
        docs=[{"_id": 1}],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}},
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1}])},
        },
        msg="aggregate should return documents with omitted readConcern",
    ),
    CommandTestCase(
        "readconcern_level_local",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern level 'local'",
    ),
    CommandTestCase(
        "readconcern_level_available",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": "available"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern level 'available'",
    ),
    CommandTestCase(
        "readconcern_level_majority",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": "majority"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern level 'majority'",
    ),
    CommandTestCase(
        "readconcern_out_local",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": "rc_out_target"}],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'local' with $out",
    ),
    CommandTestCase(
        "readconcern_out_available",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": "rc_out_target"}],
            "cursor": {},
            "readConcern": {"level": "available"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'available' with $out",
    ),
    CommandTestCase(
        "readconcern_out_majority",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": "rc_out_target"}],
            "cursor": {},
            "readConcern": {"level": "majority"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'majority' with $out",
    ),
    CommandTestCase(
        "readconcern_merge_local",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$merge": {"into": "rc_merge_target"}}],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'local' with $merge",
    ),
    CommandTestCase(
        "readconcern_merge_available",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$merge": {"into": "rc_merge_target"}}],
            "cursor": {},
            "readConcern": {"level": "available"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'available' with $merge",
    ),
    CommandTestCase(
        "readconcern_merge_majority",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$merge": {"into": "rc_merge_target"}}],
            "cursor": {},
            "readConcern": {"level": "majority"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'majority' with $merge",
    ),
]

# Property [readConcern Type Rejection]: all non-document, non-null BSON
# types for the readConcern field produce a type mismatch error.
AGGREGATE_READCONCERN_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"readconcern_type_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"aggregate should reject {tid} readConcern",
    )
    for tid, val in [
        ("string", "local"),
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

# Property [readConcern Unknown Sub-field Rejection]: unrecognized fields in the
# readConcern document are rejected.
AGGREGATE_READCONCERN_UNKNOWN_FIELD_TESTS: list[CommandTestCase] = [
    # Unknown fields in readConcern document.
    CommandTestCase(
        "rc_reject_unknown_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="aggregate should reject unknown fields in readConcern document",
    ),
    CommandTestCase(
        "rc_reject_unknown_field_case_sensitive",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"Level": "local"},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="aggregate should reject case-mismatched field names in readConcern",
    ),
]

AGGREGATE_READCONCERN_TESTS = (
    AGGREGATE_READCONCERN_ACCEPTANCE_TESTS
    + AGGREGATE_READCONCERN_TYPE_REJECTION_TESTS
    + AGGREGATE_READCONCERN_UNKNOWN_FIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_READCONCERN_TESTS))
def test_aggregate_readconcern(database_client, collection, test):
    """Test aggregate readConcern acceptance and rejection."""
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
