"""
$$CLUSTER_TIME in write commands, persistence, and under views/plan caching.

Resolved once per write command and shared across statements, except
``bulkWrite`` which advances between ops. Persisted values round-trip
byte-for-byte. Views and cached plans must re-resolve per query, not freeze at
definition time. Router-only ``runtimeConstants`` rejection is not covered.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Optional, cast

import pytest
from bson import Timestamp

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import TS_EPOCH, TS_MAX_UNSIGNED32

pytestmark = [pytest.mark.aggregate, pytest.mark.requires(cluster_time=True)]


@pytest.mark.update
def test_update_pipeline_stores_one_timestamp_for_every_document(collection):
    """Test a multi-document update pipeline writes the same timestamp everywhere."""
    collection.insert_many([{"_id": i} for i in range(25)])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": [{"$set": {"t": "$$CLUSTER_TIME"}}], "multi": True}],
        },
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": None, "values": {"$addToSet": "$t"}}},
                {
                    "$project": {
                        "_id": 0,
                        "distinct": {"$size": "$values"},
                        "kind": {"$type": {"$arrayElemAt": ["$values", 0]}},
                    }
                },
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"distinct": 1, "kind": "timestamp"}],
        msg="One update statement should write one timestamp to every matched document",
    )


@pytest.mark.update
def test_update_pipeline_shares_one_timestamp_across_statements_in_one_command(collection):
    """Test two update statements in one command observe the same cluster time."""
    collection.insert_many([{"_id": 1, "g": "first"}, {"_id": 2, "g": "second"}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"g": "first"}, "u": [{"$set": {"t": "$$CLUSTER_TIME"}}], "multi": True},
                {"q": {"g": "second"}, "u": [{"$set": {"t": "$$CLUSTER_TIME"}}], "multi": True},
            ],
        },
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": None, "values": {"$push": "$t"}}},
                {
                    "$project": {
                        "_id": 0,
                        "same": {
                            "$eq": [
                                {"$arrayElemAt": ["$values", 0]},
                                {"$arrayElemAt": ["$values", 1]},
                            ]
                        },
                    }
                },
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"same": True}],
        msg="Runtime constants are resolved once per command, so both statements agree",
    )


@pytest.mark.update
def test_update_pipeline_can_filter_on_the_variable(collection):
    """Test an update query can select documents by comparing against $$CLUSTER_TIME."""
    collection.insert_many(
        [{"_id": 1, "baseline": TS_EPOCH}, {"_id": 2, "baseline": TS_MAX_UNSIGNED32}]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"$expr": {"$lt": ["$baseline", "$$CLUSTER_TIME"]}},
                    "u": [{"$set": {"t": "$$CLUSTER_TIME"}}],
                    "multi": True,
                }
            ],
        },
    )

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"t": {"$exists": True}},
            "projection": {"_id": 1},
        },
    )

    assertSuccess(
        result,
        [{"_id": 1}],
        msg="An update query should be able to compare a stored baseline against the variable",
    )


@pytest.mark.update
def test_update_explain_with_the_variable_succeeds(collection):
    """Test explain of an update whose query and pipeline reference the variable succeeds."""
    collection.insert_one({"_id": 1, "baseline": TS_EPOCH})

    result = execute_command(
        collection,
        {
            "explain": {
                "update": collection.name,
                "updates": [
                    {
                        "q": {"$expr": {"$lt": ["$baseline", "$$CLUSTER_TIME"]}},
                        "u": [{"$set": {"t": "$$CLUSTER_TIME"}}],
                        "multi": True,
                    }
                ],
            },
            "verbosity": "queryPlanner",
        },
    )

    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="explain of a $$CLUSTER_TIME update should succeed",
    )


@pytest.mark.admin
def test_bulk_write_command_increments_per_op(collection):
    """Test the bulkWrite command resolves $$CLUSTER_TIME with a distinct increment per op."""
    collection.insert_many([{"_id": i} for i in range(3)])

    execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"_id": 0},
                    "updateMods": [{"$set": {"t": "$$CLUSTER_TIME"}}],
                },
                {
                    "update": 0,
                    "filter": {"_id": 1},
                    "updateMods": [{"$set": {"t": "$$CLUSTER_TIME"}}],
                },
                {
                    "update": 0,
                    "filter": {"_id": 2},
                    "updateMods": [{"$set": {"t": "$$CLUSTER_TIME"}}],
                },
            ],
            "nsInfo": [{"ns": f"{collection.database.name}.{collection.name}"}],
        },
    )

    agg = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": None, "values": {"$push": "$t"}}},
                {
                    "$project": {
                        "_id": 0,
                        "monotonic": {
                            "$eq": [
                                "$values",
                                {"$sortArray": {"input": "$values", "sortBy": 1}},
                            ]
                        },
                        "distinct": {"$size": {"$setUnion": ["$values"]}},
                    }
                },
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        agg,
        [{"monotonic": True, "distinct": 3}],
        msg="bulkWrite should resolve $$CLUSTER_TIME with a distinct monotonic increment per op",
    )


@pytest.mark.delete
def test_delete_can_filter_on_the_variable(collection):
    """Test a delete query can select documents by comparing against $$CLUSTER_TIME."""
    collection.insert_many(
        [{"_id": 1, "baseline": TS_EPOCH}, {"_id": 2, "baseline": TS_MAX_UNSIGNED32}]
    )
    execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"$expr": {"$lt": ["$baseline", "$$CLUSTER_TIME"]}}, "limit": 0}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "projection": {"_id": 1}})

    assertSuccess(
        result,
        [{"_id": 2}],
        msg="A delete query should be able to compare a stored baseline against the variable",
    )


@pytest.mark.update
def test_find_and_modify_pipeline_stores_a_timestamp(collection):
    """Test findAndModify with a pipeline update stores a timestamp on the matched document."""
    collection.insert_one({"_id": 1, "baseline": TS_EPOCH})
    execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"$expr": {"$lt": ["$baseline", "$$CLUSTER_TIME"]}},
            "update": [{"$set": {"t": "$$CLUSTER_TIME"}}],
        },
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 1, "kind": {"$type": "$t"}}}],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"_id": 1, "kind": "timestamp"}],
        msg="findAndModify with a pipeline update should store a timestamp",
    )


@pytest.mark.update
def test_find_and_modify_upsert_pipeline_stores_a_timestamp(collection):
    """Test a findAndModify upsert pipeline puts a timestamp on the inserted document."""
    execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": "new"},
            "update": [{"$set": {"t": "$$CLUSTER_TIME"}}],
            "upsert": True,
        },
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 1, "kind": {"$type": "$t"}}}],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"_id": "new", "kind": "timestamp"}],
        msg="A findAndModify upsert should store a timestamp on the new document",
    )


@pytest.mark.delete
def test_find_and_modify_remove_can_filter_on_the_variable(collection):
    """Test a findAndModify remove can select its document by comparing against the variable."""
    collection.insert_many([{"_id": 1, "baseline": TS_EPOCH}, {"_id": 2}])
    execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"$expr": {"$lt": ["$baseline", "$$CLUSTER_TIME"]}},
            "remove": True,
        },
    )

    result = execute_command(collection, {"find": collection.name, "projection": {"_id": 1}})

    assertSuccess(
        result,
        [{"_id": 2}],
        msg="A findAndModify remove should honor a $$CLUSTER_TIME comparison in its query",
    )


@pytest.mark.update
def test_find_and_modify_explain_with_the_variable_succeeds(collection):
    """Test explain of a findAndModify referencing the variable succeeds."""
    collection.insert_one({"_id": 1, "baseline": TS_EPOCH})

    result = execute_command(
        collection,
        {
            "explain": {
                "findAndModify": collection.name,
                "query": {"$expr": {"$lt": ["$baseline", "$$CLUSTER_TIME"]}},
                "update": [{"$set": {"t": "$$CLUSTER_TIME"}}],
            },
            "verbosity": "queryPlanner",
        },
    )

    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="explain of a $$CLUSTER_TIME findAndModify should succeed",
    )


@dataclass(frozen=True)
class PersistenceCase(BaseTestCase):
    """A write stage that should persist the timestamp the pipeline computed.

    ``build_stage`` receives the target collection name and returns the terminal
    stage; ``seed_target`` says whether the target must already hold matching
    documents for the stage to write anything.
    """

    build_stage: Optional[Callable[[str], dict[str, Any]]] = None
    seed_target: bool = False


# Property [Write Stage Persistence]: every terminal write stage stores the one
# timestamp the pipeline resolved, with no per-document re-resolution and no
# server substitution of the value.
PERSISTENCE_CASES: list[PersistenceCase] = [
    PersistenceCase(
        id="out",
        build_stage=lambda target: {"$out": target},
        msg="$out should persist one timestamp value for every written document",
    ),
    PersistenceCase(
        id="merge_replace",
        build_stage=lambda target: {"$merge": {"into": target, "whenMatched": "replace"}},
        seed_target=True,
        msg="$merge with replace should persist one timestamp value",
    ),
    PersistenceCase(
        id="merge_merge",
        build_stage=lambda target: {"$merge": {"into": target, "whenMatched": "merge"}},
        seed_target=True,
        msg="$merge with merge should persist one timestamp value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PERSISTENCE_CASES))
def test_write_stage_persists_the_computed_timestamp(collection, test: PersistenceCase):
    """Test a terminal write stage stores the timestamp the pipeline computed."""
    database = collection.database
    target = f"{collection.name}_{test.id}_target"
    collection.insert_many([{"_id": i} for i in range(5)])
    if test.seed_target:
        database[target].insert_many([{"_id": i} for i in range(5)])

    build_stage = cast(Callable[[str], dict[str, Any]], test.build_stage)
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"t": "$$CLUSTER_TIME"}},
                build_stage(target),
            ],
            "cursor": {},
        },
    )

    result = execute_command(
        database[target],
        {
            "aggregate": target,
            "pipeline": [
                {"$group": {"_id": None, "values": {"$addToSet": "$t"}}},
                {
                    "$project": {
                        "_id": 0,
                        "distinct": {"$size": "$values"},
                        "kind": {"$type": {"$arrayElemAt": ["$values", 0]}},
                    }
                },
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"distinct": 1, "kind": "timestamp"}],
        msg=test.msg,
    )


def test_merge_update_pipeline_sees_a_fresh_and_a_carried_value(collection):
    """Test a $merge update pipeline can use both a carried and a freshly resolved value."""
    database = collection.database
    collection.insert_many([{"_id": i} for i in range(5)])
    database[f"{collection.name}_merge_pipeline"].insert_many([{"_id": i} for i in range(5)])
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"carried": "$$CLUSTER_TIME"}},
                {
                    "$merge": {
                        "into": f"{collection.name}_merge_pipeline",
                        "let": {"carried": "$carried"},
                        "whenMatched": [
                            {"$set": {"carried": "$$carried", "fresh": "$$CLUSTER_TIME"}}
                        ],
                    }
                },
            ],
            "cursor": {},
        },
    )

    result = execute_command(
        database[f"{collection.name}_merge_pipeline"],
        {
            "aggregate": f"{collection.name}_merge_pipeline",
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "carried": {"$addToSet": "$carried"},
                        "fresh": {"$addToSet": "$fresh"},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "carried_values": {"$size": "$carried"},
                        "fresh_values": {"$size": "$fresh"},
                        "fresh_not_before_carried": {
                            "$gte": [
                                {"$arrayElemAt": ["$fresh", 0]},
                                {"$arrayElemAt": ["$carried", 0]},
                            ]
                        },
                    }
                },
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"carried_values": 1, "fresh_values": 1, "fresh_not_before_carried": True}],
        msg="A $merge update pipeline should see one carried and one fresh cluster time",
    )


@pytest.mark.insert
def test_stored_timestamp_is_not_the_insert_time_sentinel(collection):
    """Test a value written by an update survives as a real timestamp, not the null sentinel."""
    collection.insert_many([{"_id": i} for i in range(3)])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {},
                    "u": [{"$set": {"t": "$$CLUSTER_TIME"}}],
                    "multi": True,
                }
            ],
        },
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": None, "values": {"$addToSet": "$t"}}},
                {
                    "$project": {
                        "_id": 0,
                        "distinct": {"$size": "$values"},
                        "kind": {"$type": {"$arrayElemAt": ["$values", 0]}},
                        "is_null_sentinel": {
                            "$eq": [{"$arrayElemAt": ["$values", 0]}, Timestamp(0, 0)]
                        },
                    }
                },
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"distinct": 1, "kind": "timestamp", "is_null_sentinel": False}],
        msg="The $$CLUSTER_TIME value written by the update should survive as a real timestamp, "
        "not the null-timestamp sentinel",
    )


@pytest.mark.insert
def test_null_timestamp_sentinel_is_substituted_on_insert(collection):
    """Test a client-supplied null timestamp is server-substituted rather than stored as-is."""
    collection.insert_one({"_id": "sentinel", "t": Timestamp(0, 0)})

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"_id": "sentinel", "t": Timestamp(0, 0)},
            "projection": {"_id": 1},
        },
    )

    assertSuccess(
        result,
        [],
        msg="A client-supplied null timestamp should be server-replaced on insert",
    )


@pytest.mark.find
def test_stored_timestamp_round_trips_through_the_driver(collection):
    """Test a stored timestamp read back through the driver matches itself as a filter."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": [{"$set": {"t": "$$CLUSTER_TIME"}}], "multi": True}],
        },
    )
    stored = execute_command(collection, {"find": collection.name})["cursor"]["firstBatch"][0]["t"]

    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"t": stored}, "projection": {"_id": 1}},
    )

    assertSuccess(
        result,
        [{"_id": 1}],
        msg="A stored timestamp should round-trip through the driver without losing the increment",
    )


def test_stored_timestamp_sorts_after_earlier_timestamps(collection):
    """Test a stored cluster time sorts after earlier timestamp values in the same field."""
    collection.insert_many(
        [{"_id": 1, "t": TS_EPOCH}, {"_id": 2, "t": Timestamp(1, 1)}, {"_id": 3}]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 3}, "u": [{"$set": {"t": "$$CLUSTER_TIME"}}], "multi": False}
            ],
        },
    )

    result = execute_command(
        collection,
        {"find": collection.name, "sort": {"t": 1}, "projection": {"_id": 1}},
    )

    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 2}, {"_id": 3}],
        msg="A stored cluster time should sort after earlier timestamp values",
    )


def _view_value(collection, view_name):
    """Return the single $$CLUSTER_TIME value a view reports."""
    result = execute_command(
        collection,
        {"aggregate": view_name, "pipeline": [{"$limit": 1}], "cursor": {}},
    )
    return result["cursor"]["firstBatch"][0]["t"]


def test_repeated_pipeline_shape_is_not_constant_folded(collection):
    """Test running the same pipeline twice with a write between returns different values."""
    collection.insert_one({"_id": 1})
    pipeline = [{"$project": {"_id": 0, "t": "$$CLUSTER_TIME"}}]

    first = execute_command(
        collection, {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}}
    )["cursor"]["firstBatch"][0]["t"]
    collection.insert_one({"_id": 2})
    second = execute_command(
        collection, {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}}
    )["cursor"]["firstBatch"][0]["t"]

    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {"$project": {"_id": 0, "advanced": {"$lt": [first, second]}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"advanced": True}],
        msg="The same pipeline shape should not fold $$CLUSTER_TIME into a cached plan",
    )


def test_explain_does_not_freeze_the_value_for_later_executions(collection):
    """Test executing after an explain of the same shape still observes an advancing value."""
    collection.insert_one({"_id": 1})
    pipeline = [{"$project": {"_id": 0, "t": "$$CLUSTER_TIME"}}]

    execute_command(
        collection,
        {
            "explain": {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
            "verbosity": "queryPlanner",
        },
    )
    first = execute_command(
        collection, {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}}
    )["cursor"]["firstBatch"][0]["t"]
    collection.insert_one({"_id": 2})
    second = execute_command(
        collection, {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}}
    )["cursor"]["firstBatch"][0]["t"]

    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {"$project": {"_id": 0, "advanced": {"$lt": [first, second]}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"advanced": True}],
        msg="An explain should not bake a resolved timestamp into later executions",
    )


def test_aggregate_explain_with_the_variable_succeeds(collection):
    """Test explain of an aggregation referencing $$CLUSTER_TIME succeeds."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "explain": {
                "aggregate": collection.name,
                "pipeline": [{"$addFields": {"t": "$$CLUSTER_TIME"}}],
                "cursor": {},
            },
            "verbosity": "queryPlanner",
        },
    )

    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="explain of an aggregation referencing $$CLUSTER_TIME should succeed",
    )


@pytest.mark.find
def test_find_explain_with_the_variable_succeeds(collection):
    """Test explain of a find whose filter references $$CLUSTER_TIME succeeds."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "explain": {
                "find": collection.name,
                "filter": {"$expr": {"$gt": ["$$CLUSTER_TIME", None]}},
            },
            "verbosity": "queryPlanner",
        },
    )

    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="explain of a find referencing $$CLUSTER_TIME should succeed",
    )


def test_view_reports_one_value_within_a_single_query(collection):
    """Test a view computing $$CLUSTER_TIME reports one value for all its documents."""
    database = collection.database
    collection.insert_many([{"_id": i} for i in range(5)])
    database.command(
        {
            "create": f"{collection.name}_view",
            "viewOn": collection.name,
            "pipeline": [{"$addFields": {"t": "$$CLUSTER_TIME"}}],
        }
    )

    result = execute_command(
        collection,
        {
            "aggregate": f"{collection.name}_view",
            "pipeline": [
                {"$group": {"_id": None, "values": {"$addToSet": "$t"}}},
                {"$project": {"_id": 0, "distinct": {"$size": "$values"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"distinct": 1}],
        msg="A view should report one $$CLUSTER_TIME value within a single query",
    )


def test_view_value_is_not_frozen_at_creation_time(collection):
    """Test querying a view twice with a write between returns different values."""
    database = collection.database
    collection.insert_one({"_id": 1})
    database.command(
        {
            "create": f"{collection.name}_view",
            "viewOn": collection.name,
            "pipeline": [{"$addFields": {"t": "$$CLUSTER_TIME"}}],
        }
    )

    first = _view_value(collection, f"{collection.name}_view")
    collection.insert_one({"_id": 2})
    second = _view_value(collection, f"{collection.name}_view")

    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {"$project": {"_id": 0, "advanced": {"$lt": [first, second]}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"advanced": True}],
        msg="A stored view definition must not freeze $$CLUSTER_TIME at creation time",
    )


def test_view_on_view_value_is_not_frozen_at_creation_time(collection):
    """Test a view nested on another view still observes an advancing value."""
    database = collection.database
    collection.insert_one({"_id": 1})
    database.command(
        {
            "create": f"{collection.name}_inner_view",
            "viewOn": collection.name,
            "pipeline": [{"$addFields": {"t": "$$CLUSTER_TIME"}}],
        }
    )
    database.command(
        {
            "create": f"{collection.name}_outer_view",
            "viewOn": f"{collection.name}_inner_view",
            "pipeline": [{"$match": {}}],
        }
    )

    first = _view_value(collection, f"{collection.name}_outer_view")
    collection.insert_one({"_id": 2})
    second = _view_value(collection, f"{collection.name}_outer_view")

    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {"$project": {"_id": 0, "advanced": {"$lt": [first, second]}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"advanced": True}],
        msg="A view nested on a view must not freeze $$CLUSTER_TIME either",
    )


@pytest.mark.index
def test_indexed_comparison_returns_the_correct_result_set(collection):
    """Test an indexed timestamp field compared against $$CLUSTER_TIME selects correctly."""
    collection.insert_many([{"_id": 1, "ts": TS_EPOCH}, {"_id": 2, "ts": TS_MAX_UNSIGNED32}])
    collection.create_index([("ts", 1)])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"$expr": {"$lte": ["$ts", "$$CLUSTER_TIME"]}}},
                {"$project": {"_id": 1}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"_id": 1}],
        msg="An indexed comparison against $$CLUSTER_TIME should return the correct documents",
    )
