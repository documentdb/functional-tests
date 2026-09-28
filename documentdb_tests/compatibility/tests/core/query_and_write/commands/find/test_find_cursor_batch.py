"""Tests for find command cursor and batch size behavior."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len, Ne

# Property [Batch Size]: find batchSize controls the number of documents in firstBatch
# and interacts correctly with limit and singleBatch.
FIND_BATCH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "batchsize_zero_empty_first_batch",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"find": ctx.collection, "batchSize": 0},
        expected=[],
        msg="find should return empty firstBatch when batchSize=0.",
    ),
    CommandTestCase(
        "batchsize_one",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"find": ctx.collection, "batchSize": 1, "sort": {"_id": 1}},
        expected=[{"_id": 0}],
        msg="find should return 1 document when batchSize=1.",
    ),
    CommandTestCase(
        "batchsize_exceeds_total",
        docs=[{"_id": i} for i in range(3)],
        command=lambda ctx: {"find": ctx.collection, "batchSize": 100, "sort": {"_id": 1}},
        expected=[{"_id": 0}, {"_id": 1}, {"_id": 2}],
        msg="find should return all documents when batchSize exceeds total.",
    ),
    CommandTestCase(
        "singlebatch_true_returns_batchsize_docs",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {
            "find": ctx.collection,
            "singleBatch": True,
            "batchSize": 3,
            "sort": {"_id": 1},
        },
        expected=[{"_id": 0}, {"_id": 1}, {"_id": 2}],
        msg="find should return batchSize docs with singleBatch=true.",
    ),
    CommandTestCase(
        "batchsize_with_limit",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {
            "find": ctx.collection,
            "batchSize": 2,
            "limit": 5,
            "sort": {"_id": 1},
        },
        expected=[{"_id": 0}, {"_id": 1}],
        msg="find should return batchSize docs in first batch when limit > batchSize.",
    ),
    CommandTestCase(
        "limit_less_than_batchsize",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {
            "find": ctx.collection,
            "batchSize": 5,
            "limit": 2,
            "sort": {"_id": 1},
        },
        expected=[{"_id": 0}, {"_id": 1}],
        msg="find should return limit docs when limit < batchSize.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_BATCH_TESTS))
def test_find_batch(database_client, collection, test):
    """Test find command batch size behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )


def test_find_batchsize_zero_cursor_open(collection):
    """Test find with batchSize=0 returns non-zero cursor id."""
    collection.insert_many([{"_id": i} for i in range(5)])
    result = execute_command(collection, {"find": collection.name, "batchSize": 0})
    assertProperties(
        result,
        {"cursor.id": Ne(Int64(0))},
        raw_res=True,
        msg="find should return non-zero cursor id when batchSize=0 and docs exist.",
    )


def test_find_batchsize_exceeds_total_cursor_closed(collection):
    """Test find with batchSize > total returns cursor id = 0."""
    collection.insert_many([{"_id": i} for i in range(3)])
    result = execute_command(collection, {"find": collection.name, "batchSize": 100})
    assertProperties(
        result,
        {"cursor.id": Eq(Int64(0))},
        raw_res=True,
        msg="find should close cursor when all results fit in batchSize.",
    )


def test_find_singlebatch_true_closes_cursor(collection):
    """Test find with singleBatch=true returns cursor id = 0."""
    collection.insert_many([{"_id": i} for i in range(10)])
    result = execute_command(
        collection, {"find": collection.name, "singleBatch": True, "batchSize": 3}
    )
    assertProperties(
        result,
        {"cursor.id": Eq(Int64(0))},
        raw_res=True,
        msg="find should close cursor when singleBatch=true.",
    )


def test_find_getmore_returns_remaining(collection):
    """Test getMore after find returns remaining documents."""
    collection.insert_many([{"_id": i} for i in range(5)])
    result = execute_command(
        collection, {"find": collection.name, "batchSize": 2, "sort": {"_id": 1}}
    )
    cursor_id = result["cursor"]["id"]
    getmore_result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 10},
    )
    assertProperties(
        getmore_result,
        {"cursor": {"nextBatch": Eq([{"_id": 2}, {"_id": 3}, {"_id": 4}])}},
        raw_res=True,
        msg="getMore should return remaining documents.",
    )


def test_find_default_batchsize_cap(collection):
    """Test find default batchSize caps firstBatch at 101 documents."""
    collection.insert_many([{"_id": i} for i in range(150)])
    result = execute_command(collection, {"find": collection.name, "sort": {"_id": 1}})
    assertProperties(
        result,
        {"cursor.firstBatch": Len(101)},
        raw_res=True,
        msg="find should return at most 101 documents in default first batch.",
    )
