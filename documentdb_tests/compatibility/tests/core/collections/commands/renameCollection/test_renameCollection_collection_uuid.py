"""Tests for renameCollection collectionUUID field."""

import uuid
from datetime import datetime, timezone

import pytest
from bson import Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.binary import Binary

from documentdb_tests.compatibility.tests.core.collections.commands.renameCollection.utils.renameCollection_common import (  # noqa: E501
    cross_db_cleanup_ns,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    COLLECTION_UUID_MISMATCH_ERROR,
    INVALID_UUID_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [collectionUUID Field (Success)]: the collectionUUID field
# accepts Binary subtype 4 to validate the source collection's UUID,
# and when null, no UUID check is performed.
RENAME_COLLECTION_UUID_VALID_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_uuid_valid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "collectionUUID": ctx.uuids[ctx.collection],
        },
        expected={"ok": 1.0},
        msg="collectionUUID matching source UUID should succeed",
    ),
]

# Property [collectionUUID Field (Errors)]: when collectionUUID is a
# non-binData type, the command fails with a type mismatch error.
RENAME_COLLECTION_UUID_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"collection_uuid_type_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "collectionUUID": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collectionUUID as {tid} should produce TypeMismatch",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("string", "not-a-uuid"),
        ("array", [1]),
        ("object", {"x": 1}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(0, 1)),
        ("binary_subtype3", Binary(b"\x00" * 16, 3)),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [collectionUUID Field (UUID Mismatch)]: when collectionUUID
# is Binary subtype 4 but does not match the source collection's UUID,
# the command fails with a UUID mismatch error.
RENAME_COLLECTION_UUID_MISMATCH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_uuid_mismatch",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "collectionUUID": Binary(uuid.uuid4().bytes, 4),
        },
        error_code=COLLECTION_UUID_MISMATCH_ERROR,
        msg="collectionUUID not matching source UUID should fail",
    ),
    CommandTestCase(
        "collection_uuid_wrong_length",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "collectionUUID": Binary(b"\x00" * 8, 4),
        },
        error_code=INVALID_UUID_ERROR,
        msg="collectionUUID as Binary subtype 4 with wrong length should produce InvalidUUID",
    ),
]

RENAME_COLLECTION_UUID_TESTS: list[CommandTestCase] = (
    RENAME_COLLECTION_UUID_VALID_TESTS
    + RENAME_COLLECTION_UUID_ERROR_TESTS
    + RENAME_COLLECTION_UUID_MISMATCH_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_COLLECTION_UUID_TESTS))
def test_renameCollection_collection_uuid(database_client, collection, register_db_cleanup, test):
    """Test renameCollection collectionUUID field."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cross_db_cleanup_ns(cmd, ctx, register_db_cleanup)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
