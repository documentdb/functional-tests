"""
readConcern linearizable restriction tests.

Verifies that readConcern level 'linearizable' is accepted by read commands
and properly restricted for aggregate with $out/$merge stages.
All linearizable tests require a replica set topology.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertResult
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.requires(cluster_read_concern=True)


def test_find_accepts_linearizable(collection):
    """Test find accepts readConcern level 'linearizable'."""
    collection.insert_many([{"_id": 1, "x": 1}])
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}, "readConcern": {"level": "linearizable"}},
    )
    assertResult(result, expected=[{"_id": 1, "x": 1}], msg="find should accept linearizable.")


def test_count_accepts_linearizable(collection):
    """Test count accepts readConcern level 'linearizable'."""
    collection.insert_many([{"_id": 1}])
    result = execute_command(
        collection,
        {"count": collection.name, "query": {}, "readConcern": {"level": "linearizable"}},
    )
    assertResult(
        result, expected={"n": 1, "ok": 1.0}, msg="count should accept linearizable.", raw_res=True
    )


def test_distinct_accepts_linearizable(collection):
    """Test distinct accepts readConcern level 'linearizable'."""
    collection.insert_many([{"_id": 1, "x": "a"}])
    result = execute_command(
        collection,
        {"distinct": collection.name, "key": "x", "readConcern": {"level": "linearizable"}},
    )
    assertResult(
        result,
        expected={"ok": 1.0, "values": ["a"]},
        msg="distinct should accept linearizable.",
        raw_res=True,
    )


def test_aggregate_accepts_linearizable_simple_pipeline(collection):
    """Test aggregate accepts readConcern 'linearizable' with simple pipeline."""
    collection.insert_many([{"_id": 1, "x": 1}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"x": 1}}],
            "cursor": {},
            "readConcern": {"level": "linearizable"},
        },
    )
    assertResult(
        result,
        expected=[{"_id": 1, "x": 1}],
        msg="aggregate should accept linearizable with simple pipeline.",
    )


def test_aggregate_linearizable_rejects_out_stage(collection):
    """Test aggregate with linearizable rejects $out stage."""
    collection.insert_many([{"_id": 1}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {}}, {"$out": "output_coll"}],
            "cursor": {},
            "readConcern": {"level": "linearizable"},
        },
    )
    assertFailureCode(
        result, INVALID_OPTIONS_ERROR, msg="aggregate with linearizable should reject $out stage."
    )


def test_aggregate_linearizable_rejects_merge_stage(collection):
    """Test aggregate with linearizable rejects $merge stage."""
    collection.insert_many([{"_id": 1}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {}}, {"$merge": {"into": "output_coll"}}],
            "cursor": {},
            "readConcern": {"level": "linearizable"},
        },
    )
    assertFailureCode(
        result, INVALID_OPTIONS_ERROR, msg="aggregate with linearizable should reject $merge stage."
    )
