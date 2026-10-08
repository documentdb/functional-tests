"""$$CLUSTER_TIME invariance, monotonicity, long-lived cursors, and find reads."""

import time

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.test_constants import TS_MAX_UNSIGNED32

pytestmark = [pytest.mark.aggregate, pytest.mark.requires(cluster_time=True)]


def _noop_interval_seconds(collection):
    """Return the deployment's periodic no-op period, or None if not reported.

    The no-op is what ticks the logical clock on an idle replica set, so its
    period bounds how long an idle-advance assertion must be willing to wait.
    Reading it rather than hardcoding it keeps the wait correct on a deployment
    configured with a non-default period.
    """
    result = execute_admin_command(collection, {"getParameter": 1, "periodicNoopIntervalSecs": 1})
    if isinstance(result, Exception):
        return None
    value = result.get("periodicNoopIntervalSecs")
    return value if isinstance(value, int) and value > 0 else None


# Fold a per-document equality flag into a set: a single-element [True] proves
# every document agreed.
COLLAPSE_EQUALITY_FLAGS = [
    {"$group": {"_id": None, "flags": {"$addToSet": "$t"}}},
    {"$project": {"_id": 0, "flags": 1}},
]


def _capture_first_and_last(pipeline_middle):
    """Build a pipeline capturing the variable before and after ``pipeline_middle``."""
    return (
        [{"$addFields": {"t1": "$$CLUSTER_TIME"}}]
        + pipeline_middle
        + [
            {"$addFields": {"t2": "$$CLUSTER_TIME"}},
            {"$project": {"_id": 0, "t": {"$eq": ["$t1", "$t2"]}}},
        ]
        + COLLAPSE_EQUALITY_FLAGS
    )


def test_cluster_time_equals_itself_within_one_expression(collection):
    """Test two $$CLUSTER_TIME references in the same expression compare as equal."""
    result = execute_expression(collection, {"$eq": ["$$CLUSTER_TIME", "$$CLUSTER_TIME"]})
    assert_expression_result(
        result,
        expected=True,
        msg="Two $$CLUSTER_TIME references in one expression should be equal",
    )


def test_cluster_time_identical_across_pipeline_stages(collection):
    """Test $$CLUSTER_TIME captured in the first and last stage of a long pipeline is equal."""
    collection.insert_many([{"_id": i, "g": i % 4, "arr": [1, 2]} for i in range(20)])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": _capture_first_and_last(
                [
                    {"$sort": {"_id": 1}},
                    {"$unwind": "$arr"},
                    {"$group": {"_id": "$g", "t1": {"$first": "$t1"}, "n": {"$sum": 1}}},
                    {"$sort": {"_id": 1}},
                    {"$limit": 3},
                    {
                        "$lookup": {
                            "from": collection.name,
                            "localField": "_id",
                            "foreignField": "g",
                            "as": "joined",
                        }
                    },
                ]
            ),
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"flags": [True]}],
        msg="$$CLUSTER_TIME should be identical in the first and last stage of a pipeline",
    )


def test_cluster_time_identical_across_stages_under_delay(collection):
    """Test $$CLUSTER_TIME is unchanged across a stage that takes measurable wall-clock time."""
    collection.insert_many([{"_id": i, "g": i % 50} for i in range(400)])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": _capture_first_and_last(
                [
                    {
                        "$lookup": {
                            "from": collection.name,
                            "let": {"g": "$g"},
                            "pipeline": [{"$match": {"$expr": {"$eq": ["$g", "$$g"]}}}],
                            "as": "joined",
                        }
                    },
                    {"$sort": {"g": -1, "_id": 1}},
                ]
            ),
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"flags": [True]}],
        msg="$$CLUSTER_TIME should not be re-resolved by a slow intervening stage",
    )


def test_cluster_time_identical_in_every_stage(collection):
    """Test $$CLUSTER_TIME referenced in every stage of a pipeline yields one distinct value."""
    collection.insert_many([{"_id": i} for i in range(10)])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"a": "$$CLUSTER_TIME"}},
                {"$set": {"b": "$$CLUSTER_TIME"}},
                {"$match": {"$expr": {"$eq": ["$a", "$$CLUSTER_TIME"]}}},
                {"$addFields": {"c": "$$CLUSTER_TIME"}},
                {"$project": {"_id": 0, "seen": ["$a", "$b", "$c", "$$CLUSTER_TIME"]}},
                {"$project": {"_id": 0, "t": {"$size": {"$setUnion": ["$seen"]}}}},
            ]
            + COLLAPSE_EQUALITY_FLAGS,
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"flags": [1]}],
        msg="All $$CLUSTER_TIME references across every stage should collapse to one value",
    )


def test_cluster_time_identical_for_every_document(collection):
    """Test $$CLUSTER_TIME collapses to a single distinct value over a thousand documents."""
    collection.insert_many([{"_id": i} for i in range(1000)])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"t": "$$CLUSTER_TIME"}},
                {"$group": {"_id": None, "values": {"$addToSet": "$t"}}},
                {"$project": {"_id": 0, "distinct": {"$size": "$values"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"distinct": 1}],
        msg="$$CLUSTER_TIME should be identical for every document in one aggregation",
    )


def test_cluster_time_grouping_by_variable_yields_single_group(collection):
    """Test grouping a thousand documents by $$CLUSTER_TIME produces exactly one group."""
    collection.insert_many([{"_id": i} for i in range(1000)])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": "$$CLUSTER_TIME"}}, {"$count": "groups"}],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"groups": 1}],
        msg="Grouping by $$CLUSTER_TIME should produce a single group",
    )


def test_cluster_time_identical_inside_facet(collection):
    """Test $$CLUSTER_TIME inside $facet branches equals the value outside the facet."""
    collection.insert_many([{"_id": i} for i in range(6)])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"outer": "$$CLUSTER_TIME"}},
                {
                    "$facet": {
                        "left": [{"$project": {"_id": 0, "v": ["$outer", "$$CLUSTER_TIME"]}}],
                        "right": [{"$project": {"_id": 0, "v": ["$outer", "$$CLUSTER_TIME"]}}],
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "distinct": {
                            "$size": {
                                "$setUnion": [
                                    {
                                        "$reduce": {
                                            "input": {"$concatArrays": ["$left", "$right"]},
                                            "initialValue": [],
                                            "in": {"$concatArrays": ["$$value", "$$this.v"]},
                                        }
                                    }
                                ]
                            }
                        },
                    }
                },
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"distinct": 1}],
        msg="$$CLUSTER_TIME should be identical inside and outside $facet branches",
    )


def test_cluster_time_identical_inside_set_window_fields(collection):
    """Test $$CLUSTER_TIME in a $setWindowFields output equals the value outside the stage."""
    collection.insert_many([{"_id": i, "p": i % 3} for i in range(9)])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"outer": "$$CLUSTER_TIME"}},
                {
                    "$setWindowFields": {
                        "partitionBy": "$p",
                        "sortBy": {"_id": 1},
                        "output": {"inner": {"$max": "$$CLUSTER_TIME"}},
                    }
                },
                {"$project": {"_id": 0, "t": {"$eq": ["$outer", "$inner"]}}},
            ]
            + COLLAPSE_EQUALITY_FLAGS,
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"flags": [True]}],
        msg="$$CLUSTER_TIME in a $setWindowFields output should equal the outer value",
    )


def test_cluster_time_in_lookup_subpipeline_is_not_earlier_than_the_outer_value(collection):
    """Test $$CLUSTER_TIME in a $lookup sub-pipeline is not earlier than the outer value.

    A $lookup sub-pipeline re-resolves the variable rather than inheriting the outer value, so
    equality races under concurrent writes; ordering holds exactly and needs no tolerance.
    """
    database = collection.database
    collection.insert_many([{"_id": i} for i in range(5)])
    database[f"{collection.name}_lookup_target"].insert_many([{"_id": i} for i in range(5)])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"outer": "$$CLUSTER_TIME"}},
                {
                    "$lookup": {
                        "from": f"{collection.name}_lookup_target",
                        "pipeline": [{"$project": {"_id": 0, "inner": "$$CLUSTER_TIME"}}],
                        "as": "joined",
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "t": {
                            "$allElementsTrue": [
                                {
                                    "$map": {
                                        "input": "$joined",
                                        "as": "j",
                                        "in": {"$gte": ["$$j.inner", "$outer"]},
                                    }
                                }
                            ]
                        },
                    }
                },
            ]
            + COLLAPSE_EQUALITY_FLAGS,
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"flags": [True]}],
        msg="$$CLUSTER_TIME in a $lookup sub-pipeline should not precede the outer value",
    )


def test_cluster_time_identical_inside_union_with(collection):
    """Test $$CLUSTER_TIME added on both sides of a $unionWith yields one distinct value."""
    database = collection.database
    collection.insert_many([{"_id": i} for i in range(4)])
    database[f"{collection.name}_union_source"].insert_many([{"_id": i} for i in range(4)])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"t": "$$CLUSTER_TIME"}},
                {
                    "$unionWith": {
                        "coll": f"{collection.name}_union_source",
                        "pipeline": [{"$addFields": {"t": "$$CLUSTER_TIME"}}],
                    }
                },
                {"$group": {"_id": None, "values": {"$addToSet": "$t"}}},
                {"$project": {"_id": 0, "distinct": {"$size": "$values"}}},
            ],
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"distinct": 1}],
        msg="$$CLUSTER_TIME should be identical across both sides of a $unionWith",
    )


def test_cluster_time_identical_across_split_inducing_group(collection):
    """Test $$CLUSTER_TIME captured before and after a splitting $group stage is equal."""
    collection.insert_many([{"_id": i, "g": i % 5} for i in range(50)])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"before": "$$CLUSTER_TIME"}},
                {"$group": {"_id": "$g", "before": {"$first": "$before"}}},
                {"$sort": {"_id": 1}},
                {"$project": {"_id": 0, "t": {"$eq": ["$before", "$$CLUSTER_TIME"]}}},
            ]
            + COLLAPSE_EQUALITY_FLAGS,
            "cursor": {},
        },
    )

    assertSuccess(
        result,
        [{"flags": [True]}],
        msg="$$CLUSTER_TIME should survive a shard/merger split boundary unchanged",
    )


def test_cluster_time_identical_across_thousand_references(collection):
    """Test a thousand $$CLUSTER_TIME references in one expression resolve to one value."""
    result = execute_expression(collection, {"$size": {"$setUnion": [["$$CLUSTER_TIME"] * 1000]}})
    assert_expression_result(
        result,
        expected=1,
        msg="A thousand $$CLUSTER_TIME references should resolve to a single value",
    )


def _read_cluster_time(collection):
    """Return a single $$CLUSTER_TIME value from its own aggregation."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [{"$documents": [{}]}, {"$project": {"_id": 0, "t": "$$CLUSTER_TIME"}}],
            "cursor": {},
        },
    )
    return result["cursor"]["firstBatch"][0]["t"]


def _read_cluster_time_with_metadata(collection, command_extra=None):
    """Return the pipeline's value and the command response's own operationTime."""
    command = {
        "aggregate": 1,
        "pipeline": [{"$documents": [{}]}, {"$project": {"_id": 0, "t": "$$CLUSTER_TIME"}}],
        "cursor": {},
    }
    if command_extra:
        command.update(command_extra)
    result = execute_command(collection, command)
    return result["cursor"]["firstBatch"][0]["t"], result["operationTime"]


def test_cluster_time_advances_after_a_write(collection):
    """Test $$CLUSTER_TIME strictly advances across executions separated by a write."""
    earlier = _read_cluster_time(collection)
    collection.insert_one({"_id": "advance"})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$limit": 1},
                {"$project": {"_id": 0, "result": {"$gt": ["$$CLUSTER_TIME", earlier]}}},
            ],
            "cursor": {},
        },
    )
    assert_expression_result(
        result,
        expected=True,
        msg="$$CLUSTER_TIME should strictly advance after an intervening write",
    )


def test_cluster_time_monotonic_across_repeated_executions(collection):
    """Test a chain of executions interleaved with writes never observes a decrease."""
    observed = []
    for i in range(10):
        observed.append(_read_cluster_time(collection))
        collection.insert_one({"_id": i})

    non_decreasing = {"$eq": [{"$sortArray": {"input": observed, "sortBy": 1}}, observed]}
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$limit": 1},
                {"$project": {"_id": 0, "result": non_decreasing}},
            ],
            "cursor": {},
        },
    )
    assert_expression_result(
        result,
        expected=True,
        msg="A chain of $$CLUSTER_TIME observations should be non-decreasing",
    )


def test_cluster_time_not_frozen_across_repeated_executions(collection):
    """Test a chain of executions interleaved with writes observes at least one advance."""
    observed = []
    for i in range(10):
        observed.append(_read_cluster_time(collection))
        collection.insert_one({"_id": i})

    saw_more_than_one_value = {"$gt": [{"$size": {"$setUnion": [observed]}}, 1]}
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$limit": 1},
                {"$project": {"_id": 0, "result": saw_more_than_one_value}},
            ],
            "cursor": {},
        },
    )
    assert_expression_result(
        result,
        expected=True,
        msg="$$CLUSTER_TIME should advance across writes rather than stay frozen",
    )


def test_cluster_time_does_not_decrease_while_idle(collection):
    """Test $$CLUSTER_TIME does not go backwards over an idle interval with no writes."""
    earlier = _read_cluster_time(collection)
    time.sleep(1)

    result = execute_expression(collection, {"$gte": ["$$CLUSTER_TIME", earlier]})
    assert_expression_result(
        result,
        expected=True,
        msg="$$CLUSTER_TIME should not go backwards while the deployment is idle",
    )


@pytest.mark.slow
def test_cluster_time_strictly_advances_while_idle(collection):
    """Test $$CLUSTER_TIME strictly advances over an idle interval with no writes.

    The tick comes from the replica set's periodic no-op, so the test reads
    that period from the server rather than assuming it, and skips when the
    parameter is absent. Polling to a deadline derived from the reported
    period avoids racing the no-op's period boundary.
    """
    interval = _noop_interval_seconds(collection)
    if interval is None:
        pytest.skip("deployment does not report periodicNoopIntervalSecs")

    earlier = _read_cluster_time(collection)
    deadline = time.monotonic() + 3 * interval + 5
    advanced = False
    while time.monotonic() < deadline:
        time.sleep(1)
        if _read_cluster_time(collection) > earlier:
            advanced = True
            break

    result = execute_expression(collection, {"$literal": advanced})
    assert_expression_result(
        result,
        expected=True,
        msg="$$CLUSTER_TIME should strictly advance over an idle interval without writes",
    )


def test_cluster_time_is_not_later_than_a_following_write(collection):
    """Test the pipeline's value is not later than the operationTime of a subsequent write.

    Upper half of a bracket around the variable (paired with the preceding-write test below).
    A write issued after the read is an exact upper bound at any command speed, unlike comparing
    against the same response's own operationTime, which races under load.
    """
    value = _read_cluster_time(collection)
    write = execute_command(collection, {"insert": collection.name, "documents": [{"_id": 1}]})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$limit": 1},
                {"$project": {"_id": 0, "result": {"$lte": [value, write["operationTime"]]}}},
            ],
            "cursor": {},
        },
    )
    assert_expression_result(
        result,
        expected=True,
        msg="The variable should not follow the operationTime of a later write",
    )


def test_cluster_time_is_not_earlier_than_a_preceding_write(collection):
    """Test the pipeline's value is not earlier than a preceding write's operationTime."""
    write = execute_command(collection, {"insert": collection.name, "documents": [{"_id": 1}]})
    write_time = write["operationTime"]

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$limit": 1},
                {"$project": {"_id": 0, "result": {"$gte": ["$$CLUSTER_TIME", write_time]}}},
            ],
            "cursor": {},
        },
    )
    assert_expression_result(
        result,
        expected=True,
        msg="The variable should not precede the operationTime of an earlier write",
    )


@pytest.mark.requires(cluster_read_concern=True)
def test_cluster_time_is_not_earlier_than_after_cluster_time(collection):
    """Test a read with afterClusterTime observes a value at or after that point."""
    write = execute_command(collection, {"insert": collection.name, "documents": [{"_id": 1}]})
    after = write["operationTime"]

    pipeline_value, _ = _read_cluster_time_with_metadata(
        collection, {"readConcern": {"level": "majority", "afterClusterTime": after}}
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$limit": 1},
                {"$project": {"_id": 0, "result": {"$gte": [pipeline_value, after]}}},
            ],
            "cursor": {},
        },
    )
    assert_expression_result(
        result,
        expected=True,
        msg="A read pinned with afterClusterTime should observe a value at or after it",
    )


@pytest.mark.requires(cluster_read_concern=True)
def test_cluster_time_resolves_under_majority_read_concern(collection):
    """Test the variable resolves to a timestamp under majority read concern."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {"$project": {"_id": 0, "kind": {"$type": "$$CLUSTER_TIME"}}},
            ],
            "cursor": {},
            "readConcern": {"level": "majority"},
        },
    )

    assertSuccess(
        result,
        [{"kind": "timestamp"}],
        msg="The variable should resolve under majority read concern",
    )


@pytest.mark.requires(cluster_read_concern=True)
def test_cluster_time_resolves_under_linearizable_read_concern(collection):
    """Test the variable resolves to a timestamp under linearizable read concern."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$eq": [{"$type": "$$CLUSTER_TIME"}, "timestamp"]}},
            "projection": {"_id": 1},
            "readConcern": {"level": "linearizable"},
        },
    )

    assertSuccess(
        result,
        [{"_id": 1}],
        msg="The variable should resolve under linearizable read concern",
    )


@pytest.mark.find
def test_cluster_time_in_find_projection_identical_for_every_document(collection):
    """Test a find projection of $$CLUSTER_TIME returns one value for all documents."""
    collection.insert_many([{"_id": i} for i in range(20)])

    result = execute_command(
        collection,
        {"find": collection.name, "projection": {"_id": 0, "t": "$$CLUSTER_TIME"}},
    )

    assertSuccess(
        result,
        [{"distinct": 1}],
        msg="A find projection of $$CLUSTER_TIME should return one value for all documents",
        transform=lambda docs: [{"distinct": len({doc["t"] for doc in docs})}],
    )


@pytest.mark.find
def test_cluster_time_in_find_expr_filter_selects_earlier_timestamps(collection):
    """Test a find filter selects documents whose stored timestamp precedes $$CLUSTER_TIME."""
    earlier = _read_cluster_time(collection)
    collection.insert_many([{"_id": 1, "ts": earlier}, {"_id": 2, "ts": None}])

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$lte": ["$ts", "$$CLUSTER_TIME"]}},
            "projection": {"_id": 1},
        },
    )

    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 2}],
        msg="A find filter should compare stored timestamps against $$CLUSTER_TIME",
        ignore_doc_order=True,
    )


@pytest.mark.find
def test_cluster_time_in_find_expr_filter_excludes_later_timestamps(collection):
    """Test a find filter excludes documents whose stored timestamp follows $$CLUSTER_TIME."""
    collection.insert_many([{"_id": 1, "ts": TS_MAX_UNSIGNED32}])

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$lte": ["$ts", "$$CLUSTER_TIME"]}},
            "projection": {"_id": 1},
        },
    )

    assertSuccess(
        result,
        [],
        msg="A find filter should exclude timestamps later than $$CLUSTER_TIME",
    )


@pytest.mark.find
def test_cluster_time_in_find_computed_projection_matches_aggregation(collection):
    """Test a find computed projection of $$CLUSTER_TIME yields a timestamp-typed field."""
    collection.insert_many([{"_id": i} for i in range(3)])

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "projection": {"_id": 0, "kind": {"$type": "$$CLUSTER_TIME"}},
        },
    )

    assertSuccess(
        result,
        [{"kind": "timestamp"}, {"kind": "timestamp"}, {"kind": "timestamp"}],
        msg="A find computed projection should resolve $$CLUSTER_TIME as a timestamp",
    )


def _drain_cursor(collection, first_result, batch_size, write_between=False):
    """Collect a projected field across every batch of a cursor, optionally writing between."""
    values = [doc["t"] for doc in first_result["cursor"]["firstBatch"]]
    cursor_id = first_result["cursor"]["id"]
    writes = 0
    while cursor_id:
        if write_between:
            collection.insert_one({"_id": f"between-{writes}"})
            writes += 1
        batch = execute_command(
            collection,
            {"getMore": cursor_id, "collection": collection.name, "batchSize": batch_size},
        )
        values.extend(doc["t"] for doc in batch["cursor"]["nextBatch"])
        cursor_id = batch["cursor"]["id"]
    return values


def test_cursor_value_survives_writes_landing_between_batches(collection):
    """Test a cursor keeps one $$CLUSTER_TIME value while writes advance the deployment."""
    collection.insert_many([{"_id": i} for i in range(60)])
    first = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "t": "$$CLUSTER_TIME"}}],
            "cursor": {"batchSize": 3},
        },
    )

    values = _drain_cursor(collection, first, batch_size=3, write_between=True)

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$limit": 1},
                {"$project": {"_id": 0, "result": {"$size": {"$setUnion": [values]}}}},
            ],
            "cursor": {},
        },
    )
    assert_expression_result(
        result,
        expected=1,
        msg="Writes between batches should not change a cursor's $$CLUSTER_TIME value",
    )


def test_writes_between_batches_do_advance_the_deployment_clock(collection):
    """Test the deployment's clock demonstrably advances during the previous scenario."""
    collection.insert_many([{"_id": i} for i in range(10)])
    first = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "t": "$$CLUSTER_TIME"}}],
            "cursor": {"batchSize": 3},
        },
    )
    cursor_value = first["cursor"]["firstBatch"][0]["t"]
    _drain_cursor(collection, first, batch_size=3, write_between=True)

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$limit": 1},
                {"$project": {"_id": 0, "result": {"$gt": ["$$CLUSTER_TIME", cursor_value]}}},
            ],
            "cursor": {},
        },
    )
    assert_expression_result(
        result,
        expected=True,
        msg="The deployment clock should have advanced past the cursor's frozen value",
    )


@pytest.mark.slow
def test_idle_cursor_resumes_with_the_same_value(collection):
    """Test a cursor left idle and then resumed reports the value from its first batch."""
    collection.insert_many([{"_id": i} for i in range(10)])
    first = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "t": "$$CLUSTER_TIME"}}],
            "cursor": {"batchSize": 2},
        },
    )
    first_value = first["cursor"]["firstBatch"][0]["t"]

    time.sleep(5)
    resumed = execute_command(
        collection,
        {
            "getMore": first["cursor"]["id"],
            "collection": collection.name,
            "batchSize": 2,
        },
    )
    resumed_value = resumed["cursor"]["nextBatch"][0]["t"]

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$limit": 1},
                {"$project": {"_id": 0, "result": {"$eq": [first_value, resumed_value]}}},
            ],
            "cursor": {},
        },
    )
    assert_expression_result(
        result,
        expected=True,
        msg="An idle cursor should resume with the value from its first batch",
    )


@pytest.mark.requires(change_streams=True, cluster_time=True)
def test_change_stream_resolves_the_variable_for_its_events(collection):
    """Test a change stream whose pipeline projects $$CLUSTER_TIME yields a timestamp."""
    collection.insert_one({"_id": "seed"})
    opened = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$changeStream": {}},
                # A change stream pipeline must keep _id: it carries the resume
                # token, so the variable is added as a field rather than projected
                # into a new shape.
                {"$addFields": {"t": "$$CLUSTER_TIME"}},
            ],
            "cursor": {},
        },
    )
    collection.insert_one({"_id": "event"})
    batch = execute_command(
        collection,
        {"getMore": opened["cursor"]["id"], "collection": collection.name},
    )
    values = [doc["t"] for doc in batch["cursor"]["nextBatch"]]

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$limit": 1},
                {"$project": {"_id": 0, "result": {"$type": {"$arrayElemAt": [values, 0]}}}},
            ],
            "cursor": {},
        },
    )
    assert_expression_result(
        result,
        expected="timestamp",
        msg="A change stream should resolve $$CLUSTER_TIME for its events",
    )


@pytest.mark.requires(change_streams=True, cluster_time=True)
def test_change_stream_value_is_frozen_for_the_life_of_the_stream(collection):
    """Test a change stream reports the value from stream-open time on later events."""
    collection.insert_one({"_id": "seed"})
    opened = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$changeStream": {}},
                # A change stream pipeline must keep _id: it carries the resume
                # token, so the variable is added as a field rather than projected
                # into a new shape.
                {"$addFields": {"t": "$$CLUSTER_TIME"}},
            ],
            "cursor": {},
        },
    )
    cursor_id = opened["cursor"]["id"]

    observed = []
    for index in range(3):
        collection.insert_one({"_id": f"event-{index}"})
        batch = execute_command(collection, {"getMore": cursor_id, "collection": collection.name})
        observed.extend(doc["t"] for doc in batch["cursor"]["nextBatch"])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$limit": 1},
                {"$project": {"_id": 0, "result": {"$size": {"$setUnion": [observed]}}}},
            ],
            "cursor": {},
        },
    )
    assert_expression_result(
        result,
        expected=1,
        msg="A change stream should keep the value it resolved when the stream was opened",
    )


def test_tailable_cursor_keeps_the_value_across_get_mores(collection):
    """Test a tailable cursor on a capped collection keeps one $$CLUSTER_TIME value."""
    database = collection.database
    database.command({"create": f"{collection.name}_capped", "capped": True, "size": 8192})
    capped = database[f"{collection.name}_capped"]
    capped.insert_many([{"_id": i} for i in range(3)])

    opened = execute_command(
        collection,
        {
            "find": f"{collection.name}_capped",
            "filter": {},
            "projection": {"_id": 0, "t": "$$CLUSTER_TIME"},
            "tailable": True,
            "batchSize": 1,
        },
    )
    observed = [doc["t"] for doc in opened["cursor"]["firstBatch"]]
    cursor_id = opened["cursor"]["id"]
    for index in range(2):
        capped.insert_one({"_id": f"tail-{index}"})
        batch = execute_command(
            collection,
            {"getMore": cursor_id, "collection": f"{collection.name}_capped", "batchSize": 1},
        )
        observed.extend(doc["t"] for doc in batch["cursor"]["nextBatch"])

    result = execute_expression(collection, {"$size": {"$setUnion": [observed]}})
    assert_expression_result(
        result,
        expected=1,
        msg="A tailable cursor should keep the value it resolved when the cursor was created",
    )
