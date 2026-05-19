"""Tests for aggregate command writeConcern provenance sub-field."""

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
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [writeConcern Sub-field provenance Acceptance]: valid provenance
# enum values are accepted.
AGGREGATE_WRITECONCERN_PROVENANCE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_provenance_accept_{pid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"provenance": v},
        },
        expected={"ok": Eq(1.0)},
        msg=f"aggregate should accept provenance '{val}'",
    )
    for pid, val in [
        ("client_supplied", "clientSupplied"),
        ("implicit_default", "implicitDefault"),
        ("custom_default", "customDefault"),
        ("get_last_error_defaults", "getLastErrorDefaults"),
    ]
]

# Property [writeConcern Sub-field provenance Invalid Enum]: invalid
# provenance string values produce a bad value error.
AGGREGATE_WRITECONCERN_PROVENANCE_INVALID_ENUM_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_provenance_invalid_{pid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"provenance": v},
        },
        error_code=BAD_VALUE_ERROR,
        msg=f"aggregate should reject provenance '{val}'",
    )
    for pid, val in [
        ("unknown_string", "invalid"),
        ("empty_string", ""),
    ]
]

# Property [writeConcern Sub-field provenance Type Rejection]: non-string
# types for provenance produce a type mismatch error.
AGGREGATE_WRITECONCERN_PROVENANCE_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_provenance_reject_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"provenance": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"aggregate should reject {tid} provenance",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", [1]),
        ("document", {"a": 1}),
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

AGGREGATE_WRITECONCERN_PROVENANCE_TESTS = (
    AGGREGATE_WRITECONCERN_PROVENANCE_ACCEPTANCE_TESTS
    + AGGREGATE_WRITECONCERN_PROVENANCE_INVALID_ENUM_TESTS
    + AGGREGATE_WRITECONCERN_PROVENANCE_TYPE_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_WRITECONCERN_PROVENANCE_TESTS))
def test_aggregate_writeconcern_provenance(database_client, collection, test):
    """Test aggregate command writeConcern provenance sub-field."""
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
