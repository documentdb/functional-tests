"""Tests for explain on write operations.

Covers that explain does not modify data for update / delete / findAndModify,
and that it reports "would" statistics (nWouldModify, nWouldDelete) and the
DELETE execution stage.
"""

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.admin


def test_explain_update_does_not_modify_documents(collection):
    """Test explain on an update does not apply the modification."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    execute_command(
        collection,
        {
            "explain": {
                "update": collection.name,
                "updates": [{"q": {"a": 1}, "u": {"$set": {"b": 999}}}],
            }
        },
    )
    after = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        after, [{"_id": 1, "a": 1, "b": 1}], msg="explain update must not modify documents"
    )


def test_explain_delete_does_not_remove_documents(collection):
    """Test explain on a delete does not remove any documents."""
    collection.insert_many([{"_id": i} for i in range(5)])
    execute_command(
        collection, {"explain": {"delete": collection.name, "deletes": [{"q": {}, "limit": 0}]}}
    )
    after = execute_command(collection, {"find": collection.name, "filter": {}})
    assertSuccess(
        after,
        [{"_id": i} for i in range(5)],
        msg="explain delete must not remove documents",
        ignore_doc_order=True,
    )


def test_explain_findAndModify_does_not_modify_documents(collection):
    """Test explain on a findAndModify does not apply the modification."""
    collection.insert_one({"_id": 1, "a": 1})
    execute_command(
        collection,
        {
            "explain": {
                "findAndModify": collection.name,
                "query": {"a": 1},
                "update": {"$set": {"a": 2}},
            }
        },
    )
    after = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        after, [{"_id": 1, "a": 1}], msg="explain findAndModify must not modify documents"
    )


WOULD_STATS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="update_would_modify_count",
        docs=[{"_id": i, "a": i % 2} for i in range(6)],
        command=lambda ctx: {
            "explain": {
                "update": ctx.collection,
                "updates": [{"q": {"a": 1}, "u": {"$set": {"b": 9}}, "multi": True}],
            },
            "verbosity": "executionStats",
        },
        expected={"executionStats.executionStages.nWouldModify": Eq(3)},
        msg="explain update should report nWouldModify",
    ),
    CommandTestCase(
        id="delete_empty_collection_reports_zero",
        docs=[],
        command=lambda ctx: {
            "explain": {"delete": ctx.collection, "deletes": [{"q": {}, "limit": 0}]},
            "verbosity": "executionStats",
        },
        expected={"executionStats.executionStages.nWouldDelete": Eq(0)},
        msg="empty collection should report nWouldDelete 0",
    ),
    CommandTestCase(
        id="delete_empty_indexed_collection_reports_zero",
        docs=[],
        indexes=[IndexModel([("a", 1)], name="a_1")],
        command=lambda ctx: {
            "explain": {"delete": ctx.collection, "deletes": [{"q": {"a": 1}, "limit": 0}]},
            "verbosity": "executionStats",
        },
        expected={"executionStats.executionStages.nWouldDelete": Eq(0)},
        msg="empty indexed collection should report nWouldDelete 0",
    ),
    CommandTestCase(
        id="delete_reports_matching_count",
        docs=[{"_id": i, "a": 1 if i < 3 else 2} for i in range(5)],
        command=lambda ctx: {
            "explain": {"delete": ctx.collection, "deletes": [{"q": {"a": 1}, "limit": 0}]},
            "verbosity": "executionStats",
        },
        expected={"executionStats.executionStages.nWouldDelete": Eq(3)},
        msg="should report nWouldDelete matching the query",
    ),
    CommandTestCase(
        id="delete_shows_delete_stage",
        docs=[{"_id": i, "a": 1} for i in range(3)],
        command=lambda ctx: {
            "explain": {"delete": ctx.collection, "deletes": [{"q": {"a": 1}, "limit": 1}]},
            "verbosity": "executionStats",
        },
        expected={"executionStats.executionStages.stage": Eq("DELETE")},
        msg="explain single delete should show a DELETE stage",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WOULD_STATS_TESTS))
def test_explain_write_would_stats(collection, test):
    """Test explain on writes reports would-modify/would-delete stats and stages."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
