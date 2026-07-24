"""Tests demonstrating queryShapeHash vs planCacheShapeHash divergence for pipelines.

planCacheShapeHash considers the filter, sort, projection, and certain pipeline
stages that affect plan selection ($group, $lookup, $bucket, $replaceRoot,
$project, $sort, $count, $sortByCount, $densify, $setWindowFields).
It ignores stages like $unwind, $addFields, $limit, $skip, $set, $unset,
$sample, $out, $facet, $unionWith, $redact, $fill, and $merge.
queryShapeHash considers all stages in the pipeline.

These tests verify that two pipelines sharing the same $match but differing
in a single downstream stage produce expected hash equality/inequality based
on MongoDB's actual behavior:
  - Stages ignored by the planner leave planCacheShapeHash unchanged.
  - Stages considered by the planner change planCacheShapeHash.
  - queryShapeHash always reflects any pipeline difference.
"""

from dataclasses import dataclass, field
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Ne
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.admin


def _get_plan_cache_shape_hash(collection, pipeline: list) -> str:
    """Return queryPlanner.planCacheShapeHash from explain for an aggregate pipeline."""
    cmd: dict[str, Any] = {
        "aggregate": collection.name,
        "pipeline": pipeline,
        "cursor": {},
    }
    result = execute_command(collection, {"explain": cmd, "verbosity": "queryPlanner"})
    if isinstance(result, Exception):
        raise RuntimeError(f"explain command failed: {result}")
    # Standard format: queryPlanner at top level.
    query_planner = result.get("queryPlanner", {})
    if "planCacheShapeHash" in query_planner:
        return str(query_planner["planCacheShapeHash"])
    # Stages format ($out/$merge): nested under stages.0.$cursor.queryPlanner.
    stages = result.get("stages", [])
    if stages:
        cursor_stage = stages[0].get("$cursor", {})
        qp = cursor_stage.get("queryPlanner", {})
        if "planCacheShapeHash" in qp:
            return str(qp["planCacheShapeHash"])
    raise RuntimeError(
        f"explain did not return planCacheShapeHash in expected location; got: {result}"
    )


def _get_query_shape_hash(collection, pipeline: list) -> str:
    """Return the top-level queryShapeHash from explain for an aggregate pipeline."""
    cmd: dict[str, Any] = {
        "aggregate": collection.name,
        "pipeline": pipeline,
        "cursor": {},
    }
    result = execute_command(collection, {"explain": cmd, "verbosity": "queryPlanner"})
    if isinstance(result, Exception):
        raise RuntimeError(f"explain command failed: {result}")
    if "queryShapeHash" not in result:
        raise RuntimeError(f"explain did not return queryShapeHash; got: {result}")
    return str(result["queryShapeHash"])


@dataclass(frozen=True)
class PipelineHashCase(BaseTestCase):
    """Test case comparing hashes for two aggregate pipelines.

    Attributes:
        pipeline_a: First aggregate pipeline (baseline with only $match).
        pipeline_b: Second aggregate pipeline ($match + one additional stage).
        plan_cache_same: Whether planCacheShapeHash should match.
        query_shape_same: Whether queryShapeHash should match.
    """

    pipeline_a: tuple = field(default_factory=tuple)
    pipeline_b: tuple = field(default_factory=tuple)
    plan_cache_same: bool = True
    query_shape_same: bool = False


# ---------------------------------------------------------------------------
# Tests verifying which pipeline stages affect planCacheShapeHash when added
# after a shared $match.  Each test compares a baseline pipeline (just $match)
# against the same $match followed by one additional stage.
#
# queryShapeHash always differs when any stage is added.
# planCacheShapeHash only differs for stages the query planner considers.
# ---------------------------------------------------------------------------

PIPELINE_DIVERGENCE_TESTS: list[PipelineHashCase] = [
    # Property [Stages included in planCacheShapeHash]: these stages change
    # planCacheShapeHash when added after $match
    PipelineHashCase(
        id="group_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$group": {"_id": "$b", "c": {"$sum": 1}}}),
        plan_cache_same=False,
        query_shape_same=False,
        msg=(
            "adding $group after $match should change both planCacheShapeHash " "and queryShapeHash"
        ),
    ),
    PipelineHashCase(
        id="lookup_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=(
            {"$match": {"a": {"$gt": 0}}},
            {
                "$lookup": {
                    "from": "other",
                    "localField": "a",
                    "foreignField": "_id",
                    "as": "joined",
                }
            },
        ),
        plan_cache_same=False,
        query_shape_same=False,
        msg=("adding $lookup should change both planCacheShapeHash " "and queryShapeHash"),
    ),
    PipelineHashCase(
        id="bucket_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=(
            {"$match": {"a": {"$gt": 0}}},
            {"$bucket": {"groupBy": "$a", "boundaries": [0, 5, 10]}},
        ),
        plan_cache_same=False,
        query_shape_same=False,
        msg=("adding $bucket should change both planCacheShapeHash " "and queryShapeHash"),
    ),
    PipelineHashCase(
        id="replaceRoot_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=(
            {"$match": {"a": {"$gt": 0}}},
            {"$replaceRoot": {"newRoot": "$sub"}},
        ),
        plan_cache_same=False,
        query_shape_same=False,
        msg=("adding $replaceRoot should change both planCacheShapeHash " "and queryShapeHash"),
    ),
    PipelineHashCase(
        id="project_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$project": {"a": 1}}),
        plan_cache_same=False,
        query_shape_same=False,
        msg=("adding $project should change both planCacheShapeHash " "and queryShapeHash"),
    ),
    PipelineHashCase(
        id="sort_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$sort": {"a": 1}}),
        plan_cache_same=False,
        query_shape_same=False,
        msg=("adding $sort should change both planCacheShapeHash " "and queryShapeHash"),
    ),
    PipelineHashCase(
        id="count_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$count": "total"}),
        plan_cache_same=False,
        query_shape_same=False,
        msg=("adding $count should change both planCacheShapeHash " "and queryShapeHash"),
    ),
    PipelineHashCase(
        id="sortByCount_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$sortByCount": "$a"}),
        plan_cache_same=False,
        query_shape_same=False,
        msg=("adding $sortByCount should change both planCacheShapeHash " "and queryShapeHash"),
    ),
    PipelineHashCase(
        id="densify_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=(
            {"$match": {"a": {"$gt": 0}}},
            {"$densify": {"field": "a", "range": {"step": 1, "bounds": "full"}}},
        ),
        plan_cache_same=False,
        query_shape_same=False,
        msg=("adding $densify should change both planCacheShapeHash " "and queryShapeHash"),
    ),
    PipelineHashCase(
        id="setWindowFields_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=(
            {"$match": {"a": {"$gt": 0}}},
            {"$setWindowFields": {"sortBy": {"a": 1}, "output": {"rank": {"$rank": {}}}}},
        ),
        plan_cache_same=False,
        query_shape_same=False,
        msg=("adding $setWindowFields should change both planCacheShapeHash " "and queryShapeHash"),
    ),
    # Property [Stages ignored by planCacheShapeHash]: these stages do not change
    # planCacheShapeHash but do change queryShapeHash
    PipelineHashCase(
        id="unwind_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$unwind": "$arr"}),
        plan_cache_same=True,
        query_shape_same=False,
        msg=(
            "adding $unwind should not change planCacheShapeHash "
            "but should change queryShapeHash"
        ),
    ),
    PipelineHashCase(
        id="addFields_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=(
            {"$match": {"a": {"$gt": 0}}},
            {"$addFields": {"x": {"$add": ["$a", 1]}}},
        ),
        plan_cache_same=True,
        query_shape_same=False,
        msg=(
            "adding $addFields should not change planCacheShapeHash "
            "but should change queryShapeHash"
        ),
    ),
    PipelineHashCase(
        id="limit_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$limit": 5}),
        plan_cache_same=True,
        query_shape_same=False,
        msg=(
            "adding $limit should not change planCacheShapeHash " "but should change queryShapeHash"
        ),
    ),
    PipelineHashCase(
        id="skip_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$skip": 2}),
        plan_cache_same=True,
        query_shape_same=False,
        msg=(
            "adding $skip should not change planCacheShapeHash " "but should change queryShapeHash"
        ),
    ),
    PipelineHashCase(
        id="set_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$set": {"x": 1}}),
        plan_cache_same=True,
        query_shape_same=False,
        msg=(
            "adding $set should not change planCacheShapeHash " "but should change queryShapeHash"
        ),
    ),
    PipelineHashCase(
        id="unset_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$unset": "a"}),
        plan_cache_same=True,
        query_shape_same=False,
        msg=(
            "adding $unset should not change planCacheShapeHash " "but should change queryShapeHash"
        ),
    ),
    PipelineHashCase(
        id="sample_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$sample": {"size": 3}}),
        plan_cache_same=True,
        query_shape_same=False,
        msg=(
            "adding $sample should not change planCacheShapeHash "
            "but should change queryShapeHash"
        ),
    ),
    PipelineHashCase(
        id="out_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$out": "probe_out"}),
        plan_cache_same=True,
        query_shape_same=False,
        msg=(
            "adding $out should not change planCacheShapeHash " "but should change queryShapeHash"
        ),
    ),
    PipelineHashCase(
        id="merge_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$merge": {"into": "probe_merged"}}),
        plan_cache_same=True,
        query_shape_same=False,
        msg=(
            "adding $merge should not change planCacheShapeHash " "but should change queryShapeHash"
        ),
    ),
    PipelineHashCase(
        id="facet_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=(
            {"$match": {"a": {"$gt": 0}}},
            {"$facet": {"counts": [{"$count": "n"}]}},
        ),
        plan_cache_same=True,
        query_shape_same=False,
        msg=(
            "adding $facet should not change planCacheShapeHash " "but should change queryShapeHash"
        ),
    ),
    PipelineHashCase(
        id="unionWith_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=(
            {"$match": {"a": {"$gt": 0}}},
            {"$unionWith": {"coll": "other"}},
        ),
        plan_cache_same=True,
        query_shape_same=False,
        msg=(
            "adding $unionWith should not change planCacheShapeHash "
            "but should change queryShapeHash"
        ),
    ),
    PipelineHashCase(
        id="redact_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=({"$match": {"a": {"$gt": 0}}}, {"$redact": "$$KEEP"}),
        plan_cache_same=True,
        query_shape_same=False,
        msg=(
            "adding $redact should not change planCacheShapeHash "
            "but should change queryShapeHash"
        ),
    ),
    PipelineHashCase(
        id="fill_presence",
        pipeline_a=({"$match": {"a": {"$gt": 0}}},),
        pipeline_b=(
            {"$match": {"a": {"$gt": 0}}},
            {"$fill": {"output": {"b": {"method": "locf"}}}},
        ),
        plan_cache_same=True,
        query_shape_same=False,
        msg=(
            "adding $fill should not change planCacheShapeHash " "but should change queryShapeHash"
        ),
    ),
]


@pytest.mark.parametrize("test", pytest_params(PIPELINE_DIVERGENCE_TESTS))
def test_pipeline_plancacheshapehash_stage_sensitivity(collection, test):
    """planCacheShapeHash considers filter/sort/projection and certain pipeline stages."""
    collection.insert_many(
        [{"_id": i, "a": i % 5, "b": i % 3, "arr": [i, i + 1], "sub": {"x": i}} for i in range(20)]
    )
    hash_a = _get_plan_cache_shape_hash(collection, list(test.pipeline_a))
    hash_b = _get_plan_cache_shape_hash(collection, list(test.pipeline_b))
    check = Eq(hash_b) if test.plan_cache_same else Ne(hash_b)
    assertProperties(
        {"planCacheShapeHash": hash_a},
        {"planCacheShapeHash": check},
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(PIPELINE_DIVERGENCE_TESTS))
def test_pipeline_queryshapehash_considers_all_stages(collection, test):
    """queryShapeHash considers the full pipeline including all stages."""
    collection.insert_many(
        [{"_id": i, "a": i % 5, "b": i % 3, "arr": [i, i + 1], "sub": {"x": i}} for i in range(20)]
    )
    hash_a = _get_query_shape_hash(collection, list(test.pipeline_a))
    hash_b = _get_query_shape_hash(collection, list(test.pipeline_b))
    check = Eq(hash_b) if test.query_shape_same else Ne(hash_b)
    assertProperties(
        {"queryShapeHash": hash_a},
        {"queryShapeHash": check},
        msg=test.msg,
        raw_res=True,
    )
