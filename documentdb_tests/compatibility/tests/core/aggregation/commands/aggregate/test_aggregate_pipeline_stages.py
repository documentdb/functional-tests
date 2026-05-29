"""Representative pipeline stage wiring tests for the aggregate command.

One test per stage confirms the aggregate command correctly dispatches to
each stage implementation. Exhaustive stage behavior is tested in
core/operator/stages/.

Stages not testable on standalone (require replica set or Atlas Search):
$changeStreamSplitLargeEvent, $listSampledQueries, $listSearchIndexes,
$search, $searchMeta, $vectorSearch.
"""

from __future__ import annotations

from typing import Any

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists
from documentdb_tests.framework.target_collection import ExistingDatabase, SiblingCollection

# Property [Pipeline Stage Wiring]: the aggregate command correctly dispatches
# to each pipeline stage implementation.
AGGREGATE_STAGE_WIRING_TESTS: list[CommandTestCase] = [
    # Document transformation stages.
    CommandTestCase(
        "stage_project",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$project": {"x": 1}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"_id": 1, "x": 10}])}},
        msg="aggregate should dispatch $project stage",
    ),
    CommandTestCase(
        "stage_addFields",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": 20}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"_id": 1, "x": 10, "y": 20}])}},
        msg="aggregate should dispatch $addFields stage",
    ),
    CommandTestCase(
        "stage_set",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$set": {"y": 30}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"_id": 1, "x": 10, "y": 30}])}},
        msg="aggregate should dispatch $set stage",
    ),
    CommandTestCase(
        "stage_unset",
        docs=[{"_id": 1, "x": 10, "y": 20}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$unset": "y"}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"_id": 1, "x": 10}])}},
        msg="aggregate should dispatch $unset stage",
    ),
    CommandTestCase(
        "stage_replaceRoot",
        docs=[{"_id": 1, "nested": {"a": 1, "b": 2}}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$replaceRoot": {"newRoot": "$nested"}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"a": 1, "b": 2}])}},
        msg="aggregate should dispatch $replaceRoot stage",
    ),
    CommandTestCase(
        "stage_replaceWith",
        docs=[{"_id": 1, "nested": {"a": 1}}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$replaceWith": "$nested"}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"a": 1}])}},
        msg="aggregate should dispatch $replaceWith stage",
    ),
    # Filtering stages.
    CommandTestCase(
        "stage_match",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": 1}}],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "x": 1}, {"_id": 3, "x": 1}])},
        },
        msg="aggregate should dispatch $match stage",
    ),
    CommandTestCase(
        "stage_limit",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$limit": 2}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"_id": 1}, {"_id": 2}])}},
        msg="aggregate should dispatch $limit stage",
    ),
    CommandTestCase(
        "stage_skip",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$skip": 2}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"_id": 3}])}},
        msg="aggregate should dispatch $skip stage",
    ),
    CommandTestCase(
        "stage_redact",
        docs=[{"_id": 1, "level": 1, "data": "public"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$redact": "$$KEEP"}],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "level": 1, "data": "public"}])},
        },
        msg="aggregate should dispatch $redact stage",
    ),
    CommandTestCase(
        "stage_sample",
        docs=[{"_id": i} for i in range(100)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sample": {"size": 5}}, {"$count": "n"}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"n": 5}])}},
        msg="aggregate should dispatch $sample stage",
    ),
    # Ordering stages.
    CommandTestCase(
        "stage_sort",
        docs=[{"_id": 3, "x": 30}, {"_id": 1, "x": 10}, {"_id": 2, "x": 20}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 1, "x": 10}, {"_id": 2, "x": 20}, {"_id": 3, "x": 30}])
            },
        },
        msg="aggregate should dispatch $sort stage",
    ),
    # Grouping stages.
    CommandTestCase(
        "stage_group",
        docs=[{"_id": 1, "g": "a"}, {"_id": 2, "g": "b"}, {"_id": 3, "g": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$group": {"_id": "$g", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": "a", "count": 2}, {"_id": "b", "count": 1}])},
        },
        msg="aggregate should dispatch $group stage",
    ),
    CommandTestCase(
        "stage_bucket",
        docs=[{"_id": 1, "x": 5}, {"_id": 2, "x": 15}, {"_id": 3, "x": 25}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$bucket": {"groupBy": "$x", "boundaries": [0, 10, 20, 30], "default": "other"}}
            ],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq(
                    [{"_id": 0, "count": 1}, {"_id": 10, "count": 1}, {"_id": 20, "count": 1}]
                )
            },
        },
        msg="aggregate should dispatch $bucket stage",
    ),
    CommandTestCase(
        "stage_bucketAuto",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 3}, {"_id": 4, "x": 4}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$bucketAuto": {"groupBy": "$x", "buckets": 2}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should dispatch $bucketAuto stage",
    ),
    CommandTestCase(
        "stage_sortByCount",
        docs=[{"_id": 1, "t": "a"}, {"_id": 2, "t": "b"}, {"_id": 3, "t": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sortByCount": "$t"}],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": "a", "count": 2}, {"_id": "b", "count": 1}])},
        },
        msg="aggregate should dispatch $sortByCount stage",
    ),
    CommandTestCase(
        "stage_count",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$count": "total"}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"total": 3}])}},
        msg="aggregate should dispatch $count stage",
    ),
    # Reshaping stages.
    CommandTestCase(
        "stage_unwind",
        docs=[{"_id": 1, "arr": [1, 2, 3]}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$unwind": "$arr"}, {"$sort": {"arr": 1}}],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 1, "arr": 1}, {"_id": 1, "arr": 2}, {"_id": 1, "arr": 3}])
            },
        },
        msg="aggregate should dispatch $unwind stage",
    ),
    CommandTestCase(
        "stage_facet",
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$facet": {"all": [], "count": [{"$count": "n"}]}}],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq(
                    [{"all": [{"_id": 1, "x": 10}, {"_id": 2, "x": 20}], "count": [{"n": 2}]}]
                )
            },
        },
        msg="aggregate should dispatch $facet stage",
    ),
    # Joining stages.
    CommandTestCase(
        "stage_lookup",
        docs=[{"_id": 1, "fk": 10}],
        siblings=[SiblingCollection(suffix="_join", docs=[{"_id": 10, "val": "found"}])],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": f"{ctx.collection}_join",
                        "localField": "fk",
                        "foreignField": "_id",
                        "as": "joined",
                    }
                }
            ],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 1, "fk": 10, "joined": [{"_id": 10, "val": "found"}]}])
            },
        },
        msg="aggregate should dispatch $lookup stage",
    ),
    CommandTestCase(
        "stage_graphLookup",
        docs=[
            {"_id": 1, "name": "a", "parent": None},
            {"_id": 2, "name": "b", "parent": "a"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"_id": 2}},
                {
                    "$graphLookup": {
                        "from": ctx.collection,
                        "startWith": "$parent",
                        "connectFromField": "parent",
                        "connectToField": "name",
                        "as": "ancestors",
                    }
                },
            ],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq(
                    [
                        {
                            "_id": 2,
                            "name": "b",
                            "parent": "a",
                            "ancestors": [{"_id": 1, "name": "a", "parent": None}],
                        }
                    ]
                )
            },
        },
        msg="aggregate should dispatch $graphLookup stage",
    ),
    CommandTestCase(
        "stage_unionWith",
        docs=[{"_id": 1}],
        siblings=[SiblingCollection(suffix="_union", docs=[{"_id": 2}])],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$unionWith": f"{ctx.collection}_union"}, {"$sort": {"_id": 1}}],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1}, {"_id": 2}])},
        },
        msg="aggregate should dispatch $unionWith stage",
    ),
    # Output stages.
    CommandTestCase(
        "stage_out",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": "stage_wiring_out_target"}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="aggregate should dispatch $out stage",
    ),
    CommandTestCase(
        "stage_merge",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$merge": {"into": "stage_wiring_merge_target"}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([])}},
        msg="aggregate should dispatch $merge stage",
    ),
    # Metadata stages.
    CommandTestCase(
        "stage_collStats",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$collStats": {"count": {}}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Exists()}},
        msg="aggregate should dispatch $collStats stage",
    ),
    CommandTestCase(
        "stage_indexStats",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$indexStats": {}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Exists()}},
        msg="aggregate should dispatch $indexStats stage",
    ),
    CommandTestCase(
        "stage_planCacheStats",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$planCacheStats": {}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should dispatch $planCacheStats stage",
    ),
    # Window stages.
    CommandTestCase(
        "stage_setWindowFields",
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}, {"_id": 3, "x": 30}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {
                            "runTotal": {
                                "$sum": "$x",
                                "window": {"documents": ["unbounded", "current"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq(
                    [
                        {"_id": 1, "x": 10, "runTotal": 10},
                        {"_id": 2, "x": 20, "runTotal": 30},
                        {"_id": 3, "x": 30, "runTotal": 60},
                    ]
                )
            },
        },
        msg="aggregate should dispatch $setWindowFields stage",
    ),
    CommandTestCase(
        "stage_densify",
        docs=[{"_id": 1, "x": 0}, {"_id": 2, "x": 5}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$densify": {"field": "x", "range": {"step": 2, "bounds": [0, 5]}}},
                {"$sort": {"x": 1}},
            ],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should dispatch $densify stage",
    ),
    CommandTestCase(
        "stage_fill",
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": None}, {"_id": 3, "x": 30}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$fill": {"sortBy": {"_id": 1}, "output": {"x": {"method": "linear"}}}}],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 1, "x": 10}, {"_id": 2, "x": 20.0}, {"_id": 3, "x": 30}])
            },
        },
        msg="aggregate should dispatch $fill stage",
    ),
    # Geospatial stages.
    CommandTestCase(
        "stage_geoNear",
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        indexes=[IndexModel([("loc", "2dsphere")])],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$geoNear": {
                        "near": {"type": "Point", "coordinates": [0, 0]},
                        "distanceField": "dist",
                    }
                }
            ],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should dispatch $geoNear stage",
    ),
    # Hybrid scoring stages.
    CommandTestCase(
        "stage_rankFusion",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$rankFusion": {"input": {"pipelines": {"a": [{"$sort": {"x": 1}}]}}}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"_id": 1, "x": 10}])}},
        msg="aggregate should dispatch $rankFusion stage",
    ),
    # Collection-agnostic stages.
    CommandTestCase(
        "stage_documents",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"x": 1}, {"x": 2}]}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0), "cursor": {"firstBatch": Eq([{"x": 1}, {"x": 2}])}},
        msg="aggregate should dispatch $documents stage",
    ),
    CommandTestCase(
        "stage_listLocalSessions",
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": {}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should dispatch $listLocalSessions stage",
    ),
    CommandTestCase(
        "stage_listSessions",
        target_collection=ExistingDatabase(db_name="config"),
        command={
            "aggregate": "system.sessions",
            "pipeline": [{"$listSessions": {"allUsers": True}}, {"$limit": 1}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should dispatch $listSessions stage",
    ),
    CommandTestCase(
        "stage_querySettings",
        target_collection=ExistingDatabase(db_name="admin"),
        command={
            "aggregate": 1,
            "pipeline": [{"$querySettings": {}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should dispatch $querySettings stage",
    ),
    CommandTestCase(
        "stage_queryStats",
        target_collection=ExistingDatabase(db_name="admin"),
        command={
            "aggregate": 1,
            "pipeline": [{"$queryStats": {}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should dispatch $queryStats stage",
    ),
    CommandTestCase(
        "stage_listClusterCatalog",
        target_collection=ExistingDatabase(db_name="admin"),
        command={
            "aggregate": 1,
            "pipeline": [{"$listClusterCatalog": {}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should dispatch $listClusterCatalog stage",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_STAGE_WIRING_TESTS))
def test_aggregate_stage_wiring(
    database_client: Any, collection: Any, test: CommandTestCase
) -> None:
    """Test aggregate pipeline stage wiring."""
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
