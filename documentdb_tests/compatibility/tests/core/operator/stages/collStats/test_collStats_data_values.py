"""Tests for $collStats data value correctness."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.collStats.utils.collStats_helpers import (  # noqa: E501
    CollStatsTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists
from documentdb_tests.framework.target_collection import CappedCollection

# Property [storageStats Behavior]: storageStats returns expected values for
# empty collections, capped collections, and default/null/undefined scale.
STORAGE_STATS_BEHAVIOR_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "storage_stats_empty_collection",
        docs=[],
        pipeline=[{"$collStats": {"storageStats": {}}}],
        checks={
            "storageStats.count": Eq(0),
            "storageStats.size": Eq(0),
            "storageStats.storageSize": Exists(),
        },
        msg="empty collection should return count=0, size=0, storageSize=4096",
    ),
    CollStatsTestCase(
        "capped_fields",
        target_collection=CappedCollection(size=1_048_576, max=100),
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {}}}],
        checks={
            "storageStats.capped": Eq(True),
            "storageStats.max": Eq(100),
            "storageStats.maxSize": Eq(1_048_576),
        },
        msg="capped collection should include max and maxSize",
    ),
    CollStatsTestCase(
        "scale_factor_default",
        docs=[{"_id": i, "x": "a" * 100} for i in range(50)],
        pipeline=[{"$collStats": {"storageStats": {}}}],
        checks={"storageStats.scaleFactor": Eq(1)},
        msg="default scaleFactor should be 1 with type int32",
    ),
    CollStatsTestCase(
        "null_scale_defaults_to_one",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"storageStats": {"scale": None}}}],
        checks={"storageStats.scaleFactor": Eq(1)},
        msg="scale=null should default to scaleFactor 1",
    ),
]

# Property [count Output Type and Value]: when count: {} is specified, the
# output contains a count field of BSON int32 type whose value equals the total
# number of documents in the collection. storageStats.count and top-level
# count agree.
COUNT_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "count_empty_collection",
        docs=[],
        pipeline=[{"$collStats": {"count": {}}}],
        checks={"count": Eq(0)},
        msg="count on empty collection should be 0",
    ),
    CollStatsTestCase(
        "count_type_and_value",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[{"$collStats": {"count": {}}}],
        checks={"count": Eq(10)},
        msg="count should be int32 with value matching document count",
    ),
    CollStatsTestCase(
        "count_equivalence",
        docs=[{"_id": i} for i in range(25)],
        pipeline=[{"$collStats": {"storageStats": {"scale": 7}, "count": {}}}],
        checks={"storageStats.count": Eq(25), "count": Eq(25)},
        msg="storageStats.count should equal top-level count",
    ),
]

COLLSTATS_DATA_VALUES_TESTS: list[CollStatsTestCase] = STORAGE_STATS_BEHAVIOR_TESTS + COUNT_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(COLLSTATS_DATA_VALUES_TESTS))
def test_collStats_data_values(database_client, collection, test):
    """Test $collStats data value correctness properties."""
    coll = test.prepare(database_client, collection)
    result = execute_command(
        coll, {"aggregate": coll.name, "pipeline": test.pipeline, "cursor": {}}
    )
    test.assert_result(result)


# Property [storageStats totalIndexSize Invariant]: totalIndexSize equals the
# sum of all values in indexSizes.
@pytest.mark.aggregate
def test_collStats_data_values_total_index_size_equals_sum(collection):
    """Test that totalIndexSize equals the sum of indexSizes values."""
    collection.insert_one({"_id": 1, "x": 5, "y": 10})
    collection.create_index("x")
    collection.create_index("y")
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$collStats": {"storageStats": {}}}],
            "cursor": {},
        },
    )
    if isinstance(result, Exception):
        raise AssertionError(f"unexpected error: {result}")
    stats = result["cursor"]["firstBatch"][0]["storageStats"]
    index_sum = sum(stats["indexSizes"].values())
    assertProperties(
        result,
        {"storageStats.nindexes": Eq(3), "storageStats.totalIndexSize": Eq(index_sum)},
        msg="totalIndexSize should equal sum of indexSizes",
    )


# Property [storageStats nindexes Reflects Index Changes]: nindexes accurately
# reflects the number of indexes after creation and deletion.
@pytest.mark.aggregate
def test_collStats_data_values_nindexes_baseline(collection):
    """Test that nindexes is 1 for a fresh collection (only _id index)."""
    collection.insert_one({"_id": 1, "x": 5, "y": 10})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$collStats": {"storageStats": {}}}],
            "cursor": {},
        },
    )
    assertProperties(
        result,
        {"storageStats.nindexes": Eq(1)},
        msg="should have 1 index before creation",
    )


# Property [storageStats nindexes After Index Creation]: nindexes reflects
# newly created indexes.
@pytest.mark.aggregate
def test_collStats_data_values_nindexes_after_creation(collection):
    """Test that nindexes increases after creating indexes."""
    collection.insert_one({"_id": 1, "x": 5, "y": 10})
    collection.create_index("x")
    collection.create_index("y")
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$collStats": {"storageStats": {}}}],
            "cursor": {},
        },
    )
    assertProperties(
        result,
        {"storageStats.nindexes": Eq(3)},
        msg="should have 3 indexes after creation",
    )


# Property [storageStats nindexes After Index Deletion]: nindexes reflects
# dropped indexes.
@pytest.mark.aggregate
def test_collStats_data_values_nindexes_after_drop(collection):
    """Test that nindexes decreases after dropping an index."""
    collection.insert_one({"_id": 1, "x": 5, "y": 10})
    collection.create_index("x")
    collection.create_index("y")
    collection.drop_index("x_1")
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$collStats": {"storageStats": {}}}],
            "cursor": {},
        },
    )
    assertProperties(
        result,
        {"storageStats.nindexes": Eq(2)},
        msg="should have 2 indexes after drop",
    )
