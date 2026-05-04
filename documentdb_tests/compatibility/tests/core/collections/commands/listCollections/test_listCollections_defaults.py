"""Tests for listCollections command."""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, Len
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [Null and Missing Defaults]: when optional parameters are null
# or omitted, the command succeeds with default behavior applied.
NULL_AND_MISSING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        id="filter_null",
        command={"listCollections": 1, "filter": None},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="filter=null should succeed and return all collections",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="filter_empty",
        command={"listCollections": 1, "filter": {}},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="filter={} should succeed and return all collections",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="authorized_collections_null",
        command={"listCollections": 1, "authorizedCollections": None},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="authorizedCollections=null should default to false",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_null",
        command={"listCollections": 1, "comment": None},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="comment=null should succeed with results unaffected",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="cursor_null",
        command={"listCollections": 1, "cursor": None},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="cursor=null should apply default batching",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="cursor_empty_doc",
        command={"listCollections": 1, "cursor": {}},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="cursor={} should apply default batching",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="cursor_batch_size_null",
        command={"listCollections": 1, "cursor": {"batchSize": None}},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="cursor.batchSize=null should apply default batch size",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="read_concern_null",
        command={"listCollections": 1, "readConcern": None},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="readConcern=null should succeed",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="write_concern_null",
        command={"listCollections": 1, "writeConcern": None},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="writeConcern=null should succeed (treated as omitted)",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="max_time_ms_null",
        command={"listCollections": 1, "maxTimeMS": None},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="maxTimeMS=null should succeed with no time limit",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="name_only_null",
        command={"listCollections": 1, "nameOnly": None},
        expected={
            "ok": Eq(1.0),
            "cursor.firstBatch.0": {
                "name": Exists(),
                "type": Exists(),
                "options": Exists(),
                "info": Exists(),
                "idIndex": Exists(),
            },
        },
        msg="nameOnly=null should return documents with full fields",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="all_null",
        command={
            "listCollections": 1,
            "filter": None,
            "nameOnly": None,
            "authorizedCollections": None,
            "comment": None,
            "cursor": None,
            "readConcern": None,
            "writeConcern": None,
            "maxTimeMS": None,
        },
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="All optional parameters null should succeed with defaults",
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="all_omitted",
        command={"listCollections": 1},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
        msg="All optional parameters omitted should succeed with defaults",
    ),
]

# Property [Empty and Non-Existent Database]: listCollections on a
# database that does not exist or has no collections returns an empty
# firstBatch with cursor.id=0.
EMPTY_DATABASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="nonexistent_database",
        docs=None,
        command={"listCollections": 1},
        expected={
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(0),
            "cursor.id": Eq(INT64_ZERO),
        },
        msg="Non-existent database should return empty firstBatch with closed cursor",
    ),
    CommandTestCase(
        id="empty_database",
        docs=[],
        command={"listCollections": 1, "filter": {"name": "no_such_collection"}},
        expected={
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(0),
            "cursor.id": Eq(INT64_ZERO),
        },
        msg="Database with no matching collections should return empty firstBatch",
    ),
]

DEFAULTS_TESTS: list[CommandTestCase] = NULL_AND_MISSING_TESTS + EMPTY_DATABASE_TESTS


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(DEFAULTS_TESTS))
def test_listCollections_defaults(database_client, collection, test):
    """Test listCollections command input acceptance and output structure."""
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
