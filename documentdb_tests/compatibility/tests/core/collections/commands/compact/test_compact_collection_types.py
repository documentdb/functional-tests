"""Tests for compact command collection type acceptance."""

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ChangeStreamPreAndPostImagesCollection,
    ClusteredCollection,
    CollatedCollection,
    SystemBucketsCollection,
    SystemViewsCollection,
    TimeseriesCollection,
    ValidatedCollection,
    ViewCollection,
)

# Property [Collection Type Acceptance]: compact accepts collections
# regardless of their type, options, or indexes.
COMPACT_COLLECTION_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty",
        docs=[],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Empty collection should be accepted",
    ),
    CommandTestCase(
        "capped",
        target_collection=CappedCollection(size=4096),
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Capped collection should be accepted",
    ),
    CommandTestCase(
        "timeseries",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Timeseries collection should be accepted",
    ),
    CommandTestCase(
        "validated",
        target_collection=ValidatedCollection(),
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection with validator should be accepted",
    ),
    CommandTestCase(
        "collated",
        target_collection=CollatedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection with collation should be accepted",
    ),
    CommandTestCase(
        "change_stream_pre_and_post_images",
        target_collection=ChangeStreamPreAndPostImagesCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection with changeStreamPreAndPostImages should be accepted",
    ),
    CommandTestCase(
        "clustered",
        target_collection=ClusteredCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Clustered collection should be accepted",
    ),
    CommandTestCase(
        "ttl_index",
        docs=[{"_id": 1, "ts": None}],
        indexes=[IndexModel("ts", expireAfterSeconds=3600)],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection with TTL index should be accepted",
    ),
    CommandTestCase(
        "text_index",
        docs=[{"_id": 1, "content": "hello"}],
        indexes=[IndexModel([("content", "text")])],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection with text index should be accepted",
    ),
    CommandTestCase(
        "hashed_index",
        docs=[{"_id": 1, "a": 1}],
        indexes=[IndexModel([("a", "hashed")])],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection with hashed index should be accepted",
    ),
    CommandTestCase(
        "compound_index",
        docs=[{"_id": 1, "a": 1, "b": 2}],
        indexes=[IndexModel([("a", 1), ("b", -1)])],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection with compound index should be accepted",
    ),
    CommandTestCase(
        "2dsphere_index",
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        indexes=[IndexModel([("loc", "2dsphere")])],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection with 2dsphere index should be accepted",
    ),
    CommandTestCase(
        "wildcard_index",
        docs=[{"_id": 1, "a": 1}],
        indexes=[IndexModel([("$**", 1)])],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection with wildcard index should be accepted",
    ),
    CommandTestCase(
        "unique_index",
        docs=[{"_id": 1, "a": 1}],
        indexes=[IndexModel("a", unique=True)],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Collection with unique index should be accepted",
    ),
    CommandTestCase(
        "timeseries_buckets",
        target_collection=SystemBucketsCollection(),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Timeseries system.buckets collection should be accepted",
    ),
    CommandTestCase(
        "system_views",
        target_collection=SystemViewsCollection(),
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="system.views collection should be accepted",
    ),
]

# Property [View Rejection]: attempting to compact a view produces a
# command-not-supported-on-view error.
COMPACT_VIEW_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_rejection",
        target_collection=ViewCollection(),
        command=lambda ctx: {"compact": ctx.collection},
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="Compacting a view should be rejected",
    ),
]

COMPACT_COLLECTION_TYPE_ALL_TESTS: list[CommandTestCase] = (
    COMPACT_COLLECTION_TYPE_TESTS + COMPACT_VIEW_REJECTION_TESTS
)


@pytest.mark.requires(unforced_compact=True)
@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMPACT_COLLECTION_TYPE_ALL_TESTS))
def test_compact_collection_types(database_client, collection, test):
    """Test compact command behavior across collection types."""
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
