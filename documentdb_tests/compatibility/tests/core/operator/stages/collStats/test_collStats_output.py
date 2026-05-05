"""Tests for $collStats output structure and field presence."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.stages.collStats.utils.collStats_helpers import (  # noqa: E501
    CollStatsTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, NotExists
from documentdb_tests.framework.target_collection import ViewCollection
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [Base Output Fields]: $collStats always returns ns (string), host
# (string), and localTime (date) in the output document, and never includes
# _id. When all four sub-options are requested, all corresponding sections
# appear alongside the base fields.
BASE_OUTPUT_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "base_output_fields",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[{"$collStats": {}}],
        checks={
            "ns": IsType("string"),
            "host": IsType("string"),
            "localTime": IsType("date"),
            "_id": NotExists(),
            "storageStats": NotExists(),
            "latencyStats": NotExists(),
            "count": NotExists(),
            "queryExecStats": NotExists(),
        },
        msg="should return ns, host, and localTime with correct types and no _id",
    ),
    CollStatsTestCase(
        "all_four_options_present",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[
            {
                "$collStats": {
                    "latencyStats": {},
                    "storageStats": {},
                    "count": {},
                    "queryExecStats": {},
                }
            }
        ],
        checks={
            "ns": Exists(),
            "host": Exists(),
            "localTime": Exists(),
            "latencyStats": Exists(),
            "storageStats": Exists(),
            "count": Exists(),
            "queryExecStats": Exists(),
        },
        msg="all four sub-options should include all sections",
    ),
]

# Property [latencyStats Output Structure]: when latencyStats is requested, the
# output contains a latencyStats document with sub-documents for reads, writes,
# commands, and transactions, each containing Int64 fields latency and ops.
LATENCY_STATS_STRUCTURE_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "latency_stats_output_structure",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"latencyStats": {}}}],
        checks={
            "latencyStats.reads": Exists(),
            "latencyStats.reads.latency": IsType("long"),
            "latencyStats.reads.ops": IsType("long"),
            "latencyStats.writes": Exists(),
            "latencyStats.writes.latency": IsType("long"),
            "latencyStats.writes.ops": IsType("long"),
            "latencyStats.commands": Exists(),
            "latencyStats.commands.latency": IsType("long"),
            "latencyStats.commands.ops": IsType("long"),
            "latencyStats.transactions": Exists(),
            "latencyStats.transactions.latency": IsType("long"),
            "latencyStats.transactions.ops": IsType("long"),
        },
        msg="latencyStats should contain reads, writes, commands, "
        "transactions with latency and ops",
    ),
]

# Property [queryExecStats Output Structure]: queryExecStats contains a
# collectionScans sub-document with total and nonTailable as Int64 fields.
QUERY_EXEC_STATS_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "query_exec_stats_output_structure",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"queryExecStats": {}}}],
        checks={
            "queryExecStats.collectionScans": Exists(),
            "queryExecStats.collectionScans.total": IsType("long"),
            "queryExecStats.collectionScans.nonTailable": IsType("long"),
        },
        msg="queryExecStats should contain collectionScans with total and nonTailable as Int64",
    ),
    CollStatsTestCase(
        "query_exec_stats_empty_collection",
        docs=[],
        pipeline=[{"$collStats": {"queryExecStats": {}}}],
        checks={
            "queryExecStats.collectionScans.total": Eq(INT64_ZERO),
            "queryExecStats.collectionScans.nonTailable": Eq(INT64_ZERO),
        },
        msg="queryExecStats on empty collection should return zero counts",
    ),
    CollStatsTestCase(
        "latency_stats_empty_collection",
        docs=[],
        pipeline=[{"$collStats": {"latencyStats": {}}}],
        checks={"latencyStats": Exists()},
        msg="latencyStats on empty collection should succeed",
    ),
]

# Property [storageStats Field Presence and Types]: when storageStats is
# requested, the output contains a storageStats document with expected fields
# and correct BSON types.
STORAGE_STATS_FIELD_PRESENCE_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "storage_stats_field_presence",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[{"$collStats": {"storageStats": {}}}],
        checks={
            "storageStats.size": IsType("int"),
            "storageStats.count": IsType("int"),
            "storageStats.avgObjSize": IsType("int"),
            "storageStats.storageSize": IsType("int"),
            "storageStats.capped": IsType("bool"),
            "storageStats.nindexes": IsType("int"),
            "storageStats.indexSizes": IsType("object"),
            "storageStats.totalIndexSize": IsType("int"),
            "storageStats.totalSize": IsType("int"),
            "storageStats.scaleFactor": IsType("int"),
            "storageStats.indexBuilds": IsType("array"),
        },
        msg="storageStats should contain all expected fields with correct types",
    ),
]

# Property [latencyStats Histogram Presence]: when histograms is true, each
# latencyStats sub-document includes a histogram array; when false or omitted,
# the histogram array is absent.
LATENCY_HISTOGRAM_PRESENCE_TESTS: list[CollStatsTestCase] = [
    CollStatsTestCase(
        "histograms_true",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"latencyStats": {"histograms": True}}}],
        checks={
            "latencyStats.reads.histogram": Exists(),
            "latencyStats.writes.histogram": Exists(),
            "latencyStats.commands.histogram": Exists(),
            "latencyStats.transactions.histogram": Exists(),
        },
        msg="histograms=True should add histogram field",
    ),
    CollStatsTestCase(
        "histograms_true_on_view",
        target_collection=ViewCollection(),
        pipeline=[{"$collStats": {"latencyStats": {"histograms": True}}}],
        checks={
            "latencyStats.reads.histogram": Exists(),
            "latencyStats.writes.histogram": Exists(),
            "latencyStats.commands.histogram": Exists(),
            "latencyStats.transactions.histogram": Exists(),
        },
        msg="histograms=True on a view should add histogram field",
    ),
    CollStatsTestCase(
        "histograms_false",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"latencyStats": {"histograms": False}}}],
        checks={
            "latencyStats.reads.histogram": NotExists(),
            "latencyStats.writes.histogram": NotExists(),
            "latencyStats.commands.histogram": NotExists(),
            "latencyStats.transactions.histogram": NotExists(),
        },
        msg="histograms=False should not include histogram field",
    ),
    CollStatsTestCase(
        "histograms_omitted",
        docs=[{"_id": 1}],
        pipeline=[{"$collStats": {"latencyStats": {}}}],
        checks={
            "latencyStats.reads.histogram": NotExists(),
            "latencyStats.writes.histogram": NotExists(),
            "latencyStats.commands.histogram": NotExists(),
            "latencyStats.transactions.histogram": NotExists(),
        },
        msg="histograms omitted should not include histogram field",
    ),
]

COLLSTATS_OUTPUT_TESTS: list[CollStatsTestCase] = (
    BASE_OUTPUT_TESTS
    + LATENCY_STATS_STRUCTURE_TESTS
    + QUERY_EXEC_STATS_TESTS
    + STORAGE_STATS_FIELD_PRESENCE_TESTS
    + LATENCY_HISTOGRAM_PRESENCE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(COLLSTATS_OUTPUT_TESTS))
def test_collStats_output(database_client, collection, test):
    """Test $collStats output structure properties."""
    coll = test.prepare(database_client, collection)
    result = execute_command(
        coll, {"aggregate": coll.name, "pipeline": test.pipeline, "cursor": {}}
    )
    test.assert_result(result)


# Property [latencyStats Histogram Structure]: when histograms is true, each
# histogram entry contains exactly two Int64 fields (micros and count), entries
# are sorted ascending by micros, and entries with zero count are omitted.
@pytest.mark.aggregate
def test_collStats_output_histogram_structure(collection):
    """Test histogram entry structure, sort order, and zero-count omission."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$collStats": {"latencyStats": {"histograms": True}}}],
            "cursor": {},
        },
    )

    if isinstance(result, Exception):
        raise AssertionError(f"unexpected error: {result}")
    doc = result["cursor"]["firstBatch"][0]
    errors: list[str] = []
    for name in ["reads", "writes", "commands", "transactions"]:
        hist = doc["latencyStats"][name]["histogram"]
        for i, entry in enumerate(hist):
            if "micros" not in entry or "count" not in entry:
                errors.append(f"{name}[{i}] missing micros or count, has keys {set(entry.keys())}")
                continue
            if not isinstance(entry["micros"], Int64):
                errors.append(f"{name}[{i}].micros is not Int64")
            if not isinstance(entry["count"], Int64):
                errors.append(f"{name}[{i}].count is not Int64")
            if entry["count"] <= 0:
                errors.append(f"{name}[{i}].count is zero or negative")
        micros_vals = [e["micros"] for e in hist]
        if micros_vals != sorted(micros_vals):
            errors.append(f"{name} histogram not sorted ascending by micros")
    if not doc["latencyStats"]["writes"]["histogram"]:
        errors.append("writes histogram is empty after insert")
    if errors:
        raise AssertionError("histogram structure errors:\n  " + "\n  ".join(errors))


# Property [ns Value Correctness]: the ns field in the output matches
# <database>.<collection>.
@pytest.mark.aggregate
def test_collStats_output_ns_value(database_client, collection):
    """Test that ns matches db.collection."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection, {"aggregate": collection.name, "pipeline": [{"$collStats": {}}], "cursor": {}}
    )
    expected_ns = f"{database_client.name}.{collection.name}"
    assertProperties(result, {"ns": Eq(expected_ns)}, msg="ns should be db.collection")
