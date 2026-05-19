"""Tests for aggregate command collectionUUID parameter."""

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
    COLLECTION_UUID_MISMATCH_ERROR,
    COLLECTION_UUID_NOT_SUPPORTED_AGNOSTIC_ERROR,
    INVALID_UUID_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import NamedCollection

# Property [collectionUUID Acceptance]: valid collectionUUID values are
# accepted and the command succeeds when the UUID matches.
AGGREGATE_COLLECTION_UUID_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "uuid_correct_match",
        target_collection=NamedCollection(suffix="_uuid_target"),
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collectionUUID": ctx.uuids[ctx.collection],
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept collectionUUID matching the collection",
    ),
    CommandTestCase(
        "uuid_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collectionUUID": None,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept null collectionUUID",
    ),
]

# Property [collectionUUID Type Rejection]: invalid types for collectionUUID
# are rejected.
AGGREGATE_COLLECTION_UUID_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"uuid_reject_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "collectionUUID": v,
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"aggregate should reject {tid} collectionUUID",
        )
        for tid, val in [
            ("string", "not-a-uuid"),
            ("int32", 123),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1, 2]),
            ("document", {"x": 1}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("regex", Regex(".*")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
            ("binary_subtype0", Binary(b"hello", 0)),
        ]
    ],
    CommandTestCase(
        "uuid_reject_binary_subtype4_wrong_size",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collectionUUID": Binary(b"short", 4),
        },
        error_code=INVALID_UUID_ERROR,
        msg="aggregate should reject Binary subtype 4 with wrong size as invalid UUID",
    ),
]

# Property [collectionUUID Mismatch]: a valid UUID that does not match the
# target collection is rejected.
AGGREGATE_COLLECTION_UUID_MISMATCH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "uuid_mismatch_wrong_uuid",
        target_collection=NamedCollection(suffix="_uuid_mismatch"),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collectionUUID": Binary.from_uuid(
                __import__("uuid").UUID("12345678-1234-1234-1234-123456789abc")
            ),
        },
        error_code=COLLECTION_UUID_MISMATCH_ERROR,
        msg="aggregate should reject collectionUUID that does not match the collection",
    ),
    CommandTestCase(
        "uuid_mismatch_nonexistent_collection",
        docs=None,
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collectionUUID": Binary.from_uuid(
                __import__("uuid").UUID("12345678-1234-1234-1234-123456789abc")
            ),
        },
        error_code=COLLECTION_UUID_MISMATCH_ERROR,
        msg="aggregate should reject collectionUUID on a non-existent collection",
    ),
]

# Property [collectionUUID Agnostic Rejection]: collectionUUID is not
# supported in collection-agnostic mode.
AGGREGATE_COLLECTION_UUID_AGNOSTIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "uuid_reject_agnostic_mode",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"x": 1}]}],
            "cursor": {},
            "collectionUUID": Binary.from_uuid(
                __import__("uuid").UUID("12345678-1234-1234-1234-123456789abc")
            ),
        },
        error_code=COLLECTION_UUID_NOT_SUPPORTED_AGNOSTIC_ERROR,
        msg="aggregate should reject collectionUUID in collection-agnostic mode",
    ),
]

AGGREGATE_COLLECTION_UUID_TESTS = (
    AGGREGATE_COLLECTION_UUID_ACCEPTANCE_TESTS
    + AGGREGATE_COLLECTION_UUID_TYPE_REJECTION_TESTS
    + AGGREGATE_COLLECTION_UUID_MISMATCH_TESTS
    + AGGREGATE_COLLECTION_UUID_AGNOSTIC_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_COLLECTION_UUID_TESTS))
def test_aggregate_collection_uuid(database_client, collection, test):
    """Test aggregate collectionUUID acceptance and rejection."""
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
