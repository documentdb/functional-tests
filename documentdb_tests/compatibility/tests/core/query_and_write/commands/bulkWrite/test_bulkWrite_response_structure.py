"""Tests for bulkWrite response structure and cursor behavior."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gt, IsType, Len

BULKWRITE_RESPONSE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "response_contains_cursor_id",
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1}}]},
        expected={"cursor.id": IsType("long")},
        msg="bulkWrite response should contain a long cursor.id",
    ),
    CommandTestCase(
        "response_contains_cursor_ns",
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1}}]},
        expected={"ok": Eq(1.0), "cursor.ns": Eq("admin.$cmd.bulkWrite")},
        msg="bulkWrite response cursor.ns should be admin.$cmd.bulkWrite",
    ),
    CommandTestCase(
        "response_contains_firstBatch",
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1}}]},
        expected={
            "ok": Eq(1.0),
            "cursor.firstBatch.0.ok": Eq(1.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.n": Eq(1),
        },
        msg="bulkWrite response should contain a cursor.firstBatch array",
    ),
    CommandTestCase(
        "response_nErrors_zero_on_success",
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1}}]},
        expected={"ok": Eq(1.0), "nErrors": Eq(0)},
        msg="bulkWrite response should contain nErrors:0 on success",
    ),
    CommandTestCase(
        "response_nInserted",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1}},
                {"insert": 0, "document": {"_id": 2}},
            ],
        },
        expected={"ok": Eq(1.0), "nInserted": Eq(2)},
        msg="bulkWrite response should contain nInserted",
    ),
    CommandTestCase(
        "response_nMatched_nModified",
        docs=[{"_id": 1, "x": 10}],
        command={
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {"_id": 1}, "updateMods": {"$set": {"x": 20}}}],
        },
        expected={"ok": Eq(1.0), "nMatched": Eq(1), "nModified": Eq(1)},
        msg="bulkWrite response should contain nMatched and nModified",
    ),
    CommandTestCase(
        "response_matched_but_unmodified",
        docs=[{"_id": 1, "x": 10}],
        command={
            "bulkWrite": 1,
            # $set to the SAME value: matches the doc but changes nothing.
            "ops": [{"update": 0, "filter": {"_id": 1}, "updateMods": {"$set": {"x": 10}}}],
        },
        expected={
            "ok": Eq(1.0),
            "nMatched": Eq(1),
            "nModified": Eq(0),
            "cursor.firstBatch.0.ok": Eq(1.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.n": Eq(1),
            "cursor.firstBatch.0.nModified": Eq(0),
        },
        msg="bulkWrite no-op update should report nMatched:1/nModified:0 and per-op nModified:0",
    ),
    CommandTestCase(
        "response_nDeleted",
        docs=[{"_id": 1}],
        command={"bulkWrite": 1, "ops": [{"delete": 0, "filter": {"_id": 1}}]},
        expected={"ok": Eq(1.0), "nDeleted": Eq(1)},
        msg="bulkWrite response should contain nDeleted",
    ),
    CommandTestCase(
        "errorsOnly_false_returns_all_results",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1}},
                {"insert": 0, "document": {"_id": 2}},
            ],
            "errorsOnly": False,
        },
        expected={
            "ok": Eq(1.0),
            "nInserted": Eq(2),
            "cursor.firstBatch.0.ok": Eq(1.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.n": Eq(1),
            "cursor.firstBatch.1.ok": Eq(1.0),
            "cursor.firstBatch.1.idx": Eq(1),
            "cursor.firstBatch.1.n": Eq(1),
        },
        msg="bulkWrite errorsOnly:false should return all operation results",
    ),
    CommandTestCase(
        "errorsOnly_true_full_success_empty_firstBatch",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1}},
                {"insert": 0, "document": {"_id": 2}},
            ],
            "errorsOnly": True,
        },
        expected={"ok": Eq(1.0), "nInserted": Eq(2), "nErrors": Eq(0), "cursor.firstBatch": Len(0)},
        msg="bulkWrite errorsOnly:true on full success should return an empty firstBatch",
    ),
    CommandTestCase(
        "cursor_batchSize_1",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1}},
                {"insert": 0, "document": {"_id": 2}},
                {"insert": 0, "document": {"_id": 3}},
            ],
            "cursor": {"batchSize": 1},
            "errorsOnly": False,
        },
        expected={"cursor.firstBatch": Len(1)},
        msg="bulkWrite cursor.batchSize:1 should limit firstBatch to one result",
    ),
    CommandTestCase(
        "cursor_batchSize_zero",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1}},
                {"insert": 0, "document": {"_id": 2}},
            ],
            "cursor": {"batchSize": 0},
            "errorsOnly": False,
        },
        expected={"cursor.firstBatch": Len(0), "cursor.id": Gt(0)},
        msg="bulkWrite cursor.batchSize:0 should return an empty firstBatch with a live cursor",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BULKWRITE_RESPONSE_TESTS))
def test_bulkWrite_response_structure(database_client, collection, test):
    """Test bulkWrite response structure and cursor behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = test.build_command(ctx)
    if "nsInfo" not in command:
        command = {**command, "nsInfo": [{"ns": ctx.namespace}]}
    result = execute_admin_command(collection, command)
    assertResult(result, expected=test.build_expected(ctx), msg=test.msg, raw_res=True)


def test_bulkWrite_getMore_drains_remaining_results(collection):
    """Test a batched bulkWrite cursor (batchSize:1) is drained with getMore into nextBatch."""
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1}},
                {"insert": 0, "document": {"_id": 2}},
                {"insert": 0, "document": {"_id": 3}},
            ],
            "nsInfo": [{"ns": ns}],
            "errorsOnly": False,
            "cursor": {"batchSize": 1},
        },
    )
    cursor_id = result["cursor"]["id"]
    more = execute_admin_command(collection, {"getMore": cursor_id, "collection": "$cmd.bulkWrite"})
    assertResult(
        more,
        expected={
            "ok": Eq(1.0),
            "cursor.nextBatch": Len(2),
            "cursor.nextBatch.0.idx": Eq(1),
            "cursor.nextBatch.1.idx": Eq(2),
        },
        raw_res=True,
        msg="bulkWrite getMore should drain the remaining op results into nextBatch",
    )
