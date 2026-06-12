"""Tests for distinct command collection type acceptance."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
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

# Property [Collection Type Acceptance]: distinct produces correct results
# regardless of the underlying collection type.
DISTINCT_COLLECTION_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "regular",
        docs=[{"_id": i, "x": i % 3} for i in range(5)],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [0, 1, 2], "ok": 1.0},
        ignore_order_in=["values"],
        msg="distinct should work on a regular collection",
    ),
    CommandTestCase(
        "view",
        target_collection=ViewCollection(
            options={"pipeline": [{"$match": {"x": {"$gte": 1}}}]},
            suffix="_view",
        ),
        docs=[{"_id": i, "x": i % 3} for i in range(5)],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [1, 2], "ok": 1},
        ignore_order_in=["values"],
        msg="distinct on view should only see documents passing the view pipeline",
    ),
    CommandTestCase(
        "capped",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": i, "x": i % 3} for i in range(5)],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [0, 1, 2], "ok": 1.0},
        ignore_order_in=["values"],
        msg="distinct should work on a capped collection",
    ),
    CommandTestCase(
        "timeseries",
        target_collection=TimeseriesCollection(),
        docs=[
            {"ts": datetime(2024, 1, i, tzinfo=timezone.utc), "meta": "a", "x": i % 3}
            for i in range(1, 6)
        ],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [0, 1, 2], "ok": 1},
        ignore_order_in=["values"],
        msg="distinct should work on a timeseries collection",
    ),
    CommandTestCase(
        "clustered",
        target_collection=ClusteredCollection(),
        docs=[{"_id": i, "x": i % 3} for i in range(5)],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        expected={"values": [0, 1, 2], "ok": 1.0},
        ignore_order_in=["values"],
        msg="distinct should work on a clustered collection",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DISTINCT_COLLECTION_TYPE_TESTS))
def test_distinct_collection_types(database_client, collection, test):
    """Test distinct command collection type acceptance."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
        ignore_order_in=test.ignore_order_in,
    )
