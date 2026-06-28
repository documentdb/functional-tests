"""Tests for timeseries collection document ordering behavior."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import TimeseriesCollection

# Property [Document Ordering]: documents are returned in timeField order
# within each bucket, grouped by metaField bucket.
INTRA_BUCKET_ORDERING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "time_ordered_within_bucket",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta", "granularity": "hours"}
        ),
        docs=[
            {"time": datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), "meta": "s1", "v": 5},
            {"time": datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc), "meta": "s1", "v": 1},
            {"time": datetime(2024, 1, 1, 0, 3, tzinfo=timezone.utc), "meta": "s1", "v": 3},
        ],
        command=lambda ctx: {"find": ctx.collection, "projection": {"_id": 0, "v": 1}},
        expected=[{"v": 1}, {"v": 3}, {"v": 5}],
        msg="Should return documents in timeField order, not insertion order",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(INTRA_BUCKET_ORDERING_TESTS))
def test_timeseries_ordering(database_client, collection, test):
    """Test timeseries document ordering cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
    )


# Property [Cross-Bucket Grouping]: documents are grouped by metaField bucket
# and time-ordered within each bucket; cross-bucket order is not guaranteed.
@pytest.mark.collection_mgmt
def test_timeseries_cross_bucket_grouping(database_client, collection):
    """Test that documents are time-ordered within each bucket."""
    coll = TimeseriesCollection(
        timeseries_options={"timeField": "time", "metaField": "meta", "granularity": "hours"}
    ).resolve(database_client, collection)
    coll.insert_many(
        [
            {"time": datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), "meta": "b", "v": 1},
            {"time": datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc), "meta": "a", "v": 2},
            {"time": datetime(2024, 1, 1, 0, 2, tzinfo=timezone.utc), "meta": "b", "v": 3},
            {"time": datetime(2024, 1, 1, 0, 3, tzinfo=timezone.utc), "meta": "a", "v": 4},
        ]
    )
    result = execute_command(coll, {"find": coll.name, "projection": {"_id": 0, "meta": 1, "v": 1}})
    docs = result["cursor"]["firstBatch"]
    a_docs = [d["v"] for d in docs if d["meta"] == "a"]
    b_docs = [d["v"] for d in docs if d["meta"] == "b"]
    assertSuccess(
        {"a": a_docs, "b": b_docs},
        {"a": [2, 4], "b": [1, 3]},
        msg="Should time-order within each bucket",
        raw_res=True,
    )
