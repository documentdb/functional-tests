"""Tests for aggregate command collection type acceptance."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
    TimeseriesCollection,
    ViewCollection,
)

# Property [Collection Type Acceptance]: aggregate produces correct results
# regardless of the underlying collection type.
AGGREGATE_COLLECTION_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "regular",
        docs=[{"_id": i, "x": i % 3} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$group": {"_id": "$x", "cnt": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        expected=[{"_id": 0, "cnt": 2}, {"_id": 1, "cnt": 2}, {"_id": 2, "cnt": 1}],
        msg="aggregate should work on a regular collection",
    ),
    CommandTestCase(
        "view",
        target_collection=ViewCollection(
            options={"pipeline": [{"$match": {"status": "active"}}]},
            suffix="_view",
        ),
        docs=[
            {"_id": 1, "status": "active", "x": 10},
            {"_id": 2, "status": "inactive", "x": 20},
            {"_id": 3, "status": "active", "x": 30},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$group": {"_id": None, "total": {"$sum": "$x"}}}],
            "cursor": {},
        },
        expected=[{"_id": None, "total": 40}],
        msg="aggregate on view should compose pipelines",
    ),
    CommandTestCase(
        "capped",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": i, "x": i % 3} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$group": {"_id": "$x", "cnt": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        expected=[{"_id": 0, "cnt": 2}, {"_id": 1, "cnt": 2}, {"_id": 2, "cnt": 1}],
        msg="aggregate should work on a capped collection",
    ),
    CommandTestCase(
        "timeseries",
        target_collection=TimeseriesCollection(),
        docs=[
            {"ts": datetime(2024, 1, i, tzinfo=timezone.utc), "meta": "a", "x": i % 3}
            for i in range(1, 6)
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$group": {"_id": "$x", "cnt": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        expected=[{"_id": 0, "cnt": 1}, {"_id": 1, "cnt": 2}, {"_id": 2, "cnt": 2}],
        msg="aggregate should work on a timeseries collection",
    ),
    CommandTestCase(
        "clustered",
        target_collection=ClusteredCollection(),
        docs=[{"_id": i, "x": i % 3} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$group": {"_id": "$x", "cnt": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        expected=[{"_id": 0, "cnt": 2}, {"_id": 1, "cnt": 2}, {"_id": 2, "cnt": 1}],
        msg="aggregate should work on a clustered collection",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_COLLECTION_TYPE_TESTS))
def test_aggregate_collection_types(database_client, collection, test):
    """Test aggregate command collection type acceptance."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
