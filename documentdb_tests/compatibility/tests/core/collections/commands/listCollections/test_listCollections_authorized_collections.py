"""Tests for listCollections authorizedCollections behavior."""

import uuid
from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Eq, Exists, NotExists

# Property [authorizedCollections Success Behavior]: authorizedCollections
# accepts true and false without changing the result set for a fully
# privileged user.
AUTHORIZED_COLLECTIONS_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        id="authorized_collections_true",
        command={"listCollections": 1, "authorizedCollections": True},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Contains("name", ctx.collection),
        },
        msg="authorizedCollections=true should succeed and include collection",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="authorized_collections_false",
        command={"listCollections": 1, "authorizedCollections": False},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Contains("name", ctx.collection),
        },
        msg="authorizedCollections=false should succeed and include collection",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="authorized_collections_true_name_only_true",
        command={"listCollections": 1, "authorizedCollections": True, "nameOnly": True},
        expected={
            "ok": Eq(1.0),
            "cursor.firstBatch.0": {
                "name": Exists(),
                "type": Exists(),
                "options": NotExists(),
                "info": NotExists(),
                "idIndex": NotExists(),
            },
        },
        msg="authorizedCollections=true with nameOnly=true should return only name and type",
    ),
]

# Property [authorizedCollections Type Errors]: when
# authorizedCollections is any non-boolean BSON type, the command
# produces a TYPE_MISMATCH_ERROR with no numeric-to-bool or
# string-to-bool coercion.
AUTHORIZED_COLLECTIONS_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="authorized_collections_int32",
        command={"listCollections": 1, "authorizedCollections": 1},
        msg="authorizedCollections=int32 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_int64",
        command={"listCollections": 1, "authorizedCollections": Int64(1)},
        msg="authorizedCollections=Int64 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_double",
        command={"listCollections": 1, "authorizedCollections": 1.0},
        msg="authorizedCollections=double should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_decimal128",
        command={"listCollections": 1, "authorizedCollections": Decimal128("1")},
        msg="authorizedCollections=Decimal128 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_string",
        command={"listCollections": 1, "authorizedCollections": "true"},
        msg="authorizedCollections=string should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_array",
        command={"listCollections": 1, "authorizedCollections": [True]},
        msg="authorizedCollections=array should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_object",
        command={"listCollections": 1, "authorizedCollections": {}},
        msg="authorizedCollections=object should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_objectid",
        command=lambda _: {"listCollections": 1, "authorizedCollections": ObjectId()},
        msg="authorizedCollections=ObjectId should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_datetime",
        command={
            "listCollections": 1,
            "authorizedCollections": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        msg="authorizedCollections=datetime should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_timestamp",
        command={"listCollections": 1, "authorizedCollections": Timestamp(1, 1)},
        msg="authorizedCollections=Timestamp should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_binary",
        command={"listCollections": 1, "authorizedCollections": Binary(b"hello")},
        msg="authorizedCollections=Binary should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_binary_uuid",
        command=lambda _: {
            "listCollections": 1,
            "authorizedCollections": Binary(uuid.uuid4().bytes, 4),
        },
        msg="authorizedCollections=Binary subtype 4 (UUID) should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_regex",
        command={"listCollections": 1, "authorizedCollections": Regex(".*")},
        msg="authorizedCollections=Regex should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_code",
        command={"listCollections": 1, "authorizedCollections": Code("function(){}")},
        msg="authorizedCollections=Code should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_code_with_scope",
        command={"listCollections": 1, "authorizedCollections": Code("function(){}", {"x": 1})},
        msg="authorizedCollections=CodeWithScope should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_minkey",
        command={"listCollections": 1, "authorizedCollections": MinKey()},
        msg="authorizedCollections=MinKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="authorized_collections_maxkey",
        command={"listCollections": 1, "authorizedCollections": MaxKey()},
        msg="authorizedCollections=MaxKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
]

AUTHORIZED_COLLECTIONS_TESTS: list[CommandTestCase] = (
    AUTHORIZED_COLLECTIONS_SUCCESS_TESTS + AUTHORIZED_COLLECTIONS_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(AUTHORIZED_COLLECTIONS_TESTS))
def test_listCollections_authorized_collections(database_client, collection, test):
    """Test listCollections authorizedCollections behavior."""
    target = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(target)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
