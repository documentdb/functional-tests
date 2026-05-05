"""Tests for $collStats behavior across collection types."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.collStats.utils.collStats_helpers import (  # noqa: E501
    CollStatsTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, NotExists
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    NamedCollection,
    SystemViewsCollection,
    TimeseriesCollection,
    ViewCollection,
)

# Property [Null Bypasses View Errors]: setting storageStats, count, or
# queryExecStats to null on a view bypasses the view error that would otherwise
# occur, returning only base fields.
NULL_BYPASSES_VIEW_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "storageStats_null_on_view",
        target_collection=ViewCollection(),
        pipeline=[{"$collStats": {"storageStats": None}}],
        checks={"storageStats": NotExists()},
        msg="storageStats=null on a view should succeed with base fields only",
    ),
    CollStatsTestCase(
        "count_null_on_view",
        target_collection=ViewCollection(),
        pipeline=[{"$collStats": {"count": None}}],
        checks={"count": NotExists()},
        msg="count=null on a view should succeed with base fields only",
    ),
    CollStatsTestCase(
        "queryExecStats_null_on_view",
        target_collection=ViewCollection(),
        pipeline=[{"$collStats": {"queryExecStats": None}}],
        checks={"queryExecStats": NotExists()},
        msg="queryExecStats=null on a view should succeed with base fields only",
    ),
]

# Property [Non-Existent Collection Behavior]: on a non-existent collection,
# empty $collStats and latencyStats succeed (returning base fields or
# latencyStats), while storageStats, count, and queryExecStats produce
# NAMESPACE_NOT_FOUND_ERROR. Setting any of those three to null bypasses the
# error, returning only base fields.
NONEXISTENT_COLLECTION_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "nonexistent_empty_doc",
        pipeline=[{"$collStats": {}}],
        checks={"ns": Exists(), "host": Exists(), "localTime": Exists()},
        msg="empty $collStats on non-existent collection should succeed",
    ),
    CollStatsTestCase(
        "nonexistent_latencyStats",
        pipeline=[{"$collStats": {"latencyStats": {}}}],
        checks={"latencyStats": Exists()},
        msg="latencyStats on non-existent collection should succeed",
    ),
    CollStatsTestCase(
        "nonexistent_storageStats_error",
        pipeline=[{"$collStats": {"storageStats": {}}}],
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="storageStats on non-existent collection should fail",
    ),
    CollStatsTestCase(
        "nonexistent_count_error",
        pipeline=[{"$collStats": {"count": {}}}],
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="count on non-existent collection should fail",
    ),
    CollStatsTestCase(
        "nonexistent_queryExecStats_error",
        pipeline=[{"$collStats": {"queryExecStats": {}}}],
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="queryExecStats on non-existent collection should fail",
    ),
    CollStatsTestCase(
        "storageStats_null_on_nonexistent",
        pipeline=[{"$collStats": {"storageStats": None}}],
        checks={"storageStats": NotExists()},
        msg="'storageStats'=null on non-existent collection should succeed",
    ),
    CollStatsTestCase(
        "count_null_on_nonexistent",
        pipeline=[{"$collStats": {"count": None}}],
        checks={"count": NotExists()},
        msg="'count'=null on non-existent collection should succeed",
    ),
    CollStatsTestCase(
        "queryExecStats_null_on_nonexistent",
        pipeline=[{"$collStats": {"queryExecStats": None}}],
        checks={"queryExecStats": NotExists()},
        msg="'queryExecStats'=null on non-existent collection should succeed",
    ),
]

# Property [View Errors]: storageStats, count, and queryExecStats on a view
# (including view-on-view) produce COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR;
# latencyStats succeeds on views.
VIEW_ERROR_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "storageStats_on_view",
        target_collection=ViewCollection(),
        pipeline=[{"$collStats": {"storageStats": {}}}],
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="'storageStats' on a view should be rejected",
    ),
    CollStatsTestCase(
        "count_on_view",
        target_collection=ViewCollection(),
        pipeline=[{"$collStats": {"count": {}}}],
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="'count' on a view should be rejected",
    ),
    CollStatsTestCase(
        "queryExecStats_on_view",
        target_collection=ViewCollection(),
        pipeline=[{"$collStats": {"queryExecStats": {}}}],
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="'queryExecStats' on a view should be rejected",
    ),
]

_TS_DOC = {"ts": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "a", "val": 1}


# Property [Time Series queryExecStats]: queryExecStats works normally on time
# series collections, returning the standard queryExecStats structure.
TIMESERIES_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "latency_stats",
        target_collection=TimeseriesCollection(),
        docs=[_TS_DOC],
        pipeline=[{"$collStats": {"latencyStats": {}}}],
        checks={"latencyStats": Exists()},
        msg="latencyStats should work on time series collections",
    ),
    CollStatsTestCase(
        "storage_stats_timeseries_subdoc",
        target_collection=TimeseriesCollection(),
        docs=[_TS_DOC],
        pipeline=[{"$collStats": {"storageStats": {}}}],
        checks={"storageStats.timeseries": Exists()},
        msg="storageStats.timeseries should be present",
    ),
    CollStatsTestCase(
        "storage_stats_missing_fields",
        target_collection=TimeseriesCollection(),
        docs=[_TS_DOC],
        pipeline=[{"$collStats": {"storageStats": {}}}],
        checks={
            "storageStats.count": NotExists(),
            "storageStats.avgObjSize": NotExists(),
        },
        msg="storageStats on time series should lack count and avgObjSize",
    ),
    CollStatsTestCase(
        "query_exec_stats",
        target_collection=TimeseriesCollection(),
        docs=[_TS_DOC],
        pipeline=[{"$collStats": {"queryExecStats": {}}}],
        checks={
            "queryExecStats": Exists(),
            "queryExecStats.collectionScans.total": Exists(),
            "queryExecStats.collectionScans.nonTailable": Exists(),
        },
        msg="queryExecStats should work on time series collections",
    ),
]

# Property [Non-latencyStats Collection Type Compatibility]: storageStats,
# count, and queryExecStats succeed on capped collections, system collections,
# and collections with unicode/emoji names.
COLLECTION_TYPE_COMPAT_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "latencyStats_on_view",
        target_collection=ViewCollection(),
        pipeline=[{"$collStats": {"latencyStats": {}}}],
        checks={
            "latencyStats.reads": Exists(),
            "latencyStats.writes": Exists(),
            "latencyStats.commands": Exists(),
            "latencyStats.transactions": Exists(),
        },
        msg="latencyStats on a view should have the standard 4-subdoc structure",
    ),
    CollStatsTestCase(
        "latencyStats_on_capped",
        target_collection=CappedCollection(size=1_048_576),
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"latencyStats": {}}}],
        checks={"latencyStats": Exists()},
        msg="latencyStats should work on a capped collection",
    ),
    CollStatsTestCase(
        "storageStats_on_capped",
        target_collection=CappedCollection(size=1_048_576),
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {}}}],
        checks={"storageStats": Exists()},
        msg="storageStats should work on a capped collection",
    ),
    CollStatsTestCase(
        "count_on_capped",
        target_collection=CappedCollection(size=1_048_576),
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"count": {}}}],
        checks={"count": Eq(1)},
        msg="count on a capped collection should return correct value",
    ),
    CollStatsTestCase(
        "queryExecStats_on_capped",
        target_collection=CappedCollection(size=1_048_576),
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"queryExecStats": {}}}],
        checks={"queryExecStats": Exists()},
        msg="queryExecStats should work on a capped collection",
    ),
    CollStatsTestCase(
        "latencyStats_on_unicode",
        target_collection=NamedCollection(suffix="_\u6d4b\u8bd5_\U0001f389"),
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"latencyStats": {}}}],
        checks={"latencyStats": Exists()},
        msg="latencyStats should work on unicode name",
    ),
    CollStatsTestCase(
        "storageStats_on_unicode",
        target_collection=NamedCollection(suffix="_\u6d4b\u8bd5_\U0001f389"),
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {}}}],
        checks={"storageStats": Exists()},
        msg="storageStats should work on unicode name",
    ),
    CollStatsTestCase(
        "count_on_unicode",
        target_collection=NamedCollection(suffix="_\u6d4b\u8bd5_\U0001f389"),
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"count": {}}}],
        checks={"count": Exists()},
        msg="count should work on unicode name",
    ),
    CollStatsTestCase(
        "queryExecStats_on_unicode",
        target_collection=NamedCollection(suffix="_\u6d4b\u8bd5_\U0001f389"),
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"queryExecStats": {}}}],
        checks={"queryExecStats": Exists()},
        msg="queryExecStats should work on unicode name",
    ),
    CollStatsTestCase(
        "latencyStats_on_system_views",
        target_collection=SystemViewsCollection(),
        pipeline=[{"$collStats": {"latencyStats": {}}}],
        checks={"latencyStats": Exists()},
        msg="latencyStats should work on system.views",
    ),
    CollStatsTestCase(
        "storageStats_on_system_views",
        target_collection=SystemViewsCollection(),
        pipeline=[{"$collStats": {"storageStats": {}}}],
        checks={"storageStats": Exists()},
        msg="storageStats should work on system.views",
    ),
    CollStatsTestCase(
        "count_on_system_views",
        target_collection=SystemViewsCollection(),
        pipeline=[{"$collStats": {"count": {}}}],
        checks={"count": Exists()},
        msg="count should work on system.views",
    ),
    CollStatsTestCase(
        "queryExecStats_on_system_views",
        target_collection=SystemViewsCollection(),
        pipeline=[{"$collStats": {"queryExecStats": {}}}],
        checks={"queryExecStats": Exists()},
        msg="queryExecStats should work on system.views",
    ),
]

COLLSTATS_COLLECTION_TYPE_TESTS: list[CollStatsTestCase] = (
    NULL_BYPASSES_VIEW_TESTS
    + NONEXISTENT_COLLECTION_TESTS
    + VIEW_ERROR_TESTS
    + TIMESERIES_TESTS
    + COLLECTION_TYPE_COMPAT_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(COLLSTATS_COLLECTION_TYPE_TESTS))
def test_collStats_collection_types(database_client, collection, test):
    """Test $collStats behavior across collection types."""
    coll = test.prepare(database_client, collection)
    result = execute_command(
        coll, {"aggregate": coll.name, "pipeline": test.pipeline, "cursor": {}}
    )
    test.assert_result(result)


# Property [View-on-View Errors]: storageStats, count, and queryExecStats on
# a view-on-view produce COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR.
@pytest.mark.aggregate
@pytest.mark.parametrize("sub_option", ["storageStats", "count", "queryExecStats"])
def test_collStats_collection_types_view_on_view_error(database_client, collection, sub_option):
    """Test that storageStats/count/queryExecStats on a view-on-view produce error 166."""
    collection.insert_one({"_id": 1})
    inner_view = f"{collection.name}_inner_view"
    outer_view = f"{collection.name}_outer_view"
    database_client.command({"create": inner_view, "viewOn": collection.name, "pipeline": []})
    database_client.command({"create": outer_view, "viewOn": inner_view, "pipeline": []})

    result = execute_command(
        database_client[outer_view],
        {
            "aggregate": database_client[outer_view].name,
            "pipeline": [{"$collStats": {sub_option: {}}}],
            "cursor": {},
        },
    )

    assertFailureCode(
        result,
        COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg=f"$collStats {sub_option!r} on a view-on-view should be rejected",
    )


# Property [Time Series storageStats Scale Invariance]: the timeseries
# sub-document in storageStats is NOT affected by the scale factor.
@pytest.mark.aggregate
def test_collStats_collection_types_timeseries_scale_invariance(database_client, collection):
    """Test that the timeseries sub-document is unaffected by scale."""
    ts_coll = TimeseriesCollection().resolve(database_client, collection)
    ts_coll.insert_one(_TS_DOC)
    base = execute_command(
        ts_coll,
        {
            "aggregate": ts_coll.name,
            "pipeline": [{"$collStats": {"storageStats": {}}}],
            "cursor": {},
        },
    )
    scaled = execute_command(
        ts_coll,
        {
            "aggregate": ts_coll.name,
            "pipeline": [{"$collStats": {"storageStats": {"scale": 2}}}],
            "cursor": {},
        },
    )
    if isinstance(base, Exception):
        raise AssertionError(f"unexpected error: {base}")
    base_ts = base["cursor"]["firstBatch"][0]["storageStats"]["timeseries"]
    assertProperties(
        scaled,
        {"storageStats.timeseries": Eq(base_ts)},
        msg="timeseries sub-doc should be unaffected by scale factor",
    )


# Property [Time Series Count Returns Bucket Count]: count on a time series
# collection returns the bucket count, not the measurement count.
@pytest.mark.aggregate
def test_collStats_collection_types_timeseries_bucket_count(database_client, collection):
    """Test that count returns bucket count, not measurement count."""
    ts_coll = TimeseriesCollection(granularity="hours").resolve(database_client, collection)
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    ts_coll.insert_many(
        [{"ts": base + timedelta(minutes=i), "meta": "a", "val": i} for i in range(10)]
    )
    bucket_count = database_client[f"system.buckets.{ts_coll.name}"].count_documents({})
    result = execute_command(
        ts_coll,
        {"aggregate": ts_coll.name, "pipeline": [{"$collStats": {"count": {}}}], "cursor": {}},
    )
    assertProperties(result, {"count": Eq(bucket_count)}, msg="should return bucket count")
