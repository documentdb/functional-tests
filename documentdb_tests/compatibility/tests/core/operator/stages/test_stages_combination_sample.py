"""Tests for $sample composing with other pipeline stages."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Composition]: $sample composes correctly with other
# aggregation stages, operating on its input stream and producing the expected
# document count and structure.
SAMPLE_PIPELINE_COMPOSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "position_after_match",
        docs=[{"_id": i, "v": i % 2} for i in range(10)],
        pipeline=[
            {"$match": {"v": 1}},
            {"$sample": {"size": 3}},
            {"$count": "n"},
        ],
        expected=[{"n": 3}],
        msg="$sample should operate on the $match output, not the full collection",
    ),
    StageTestCase(
        "position_after_project",
        docs=[{"_id": i, "v": i} for i in range(10)],
        pipeline=[
            {"$project": {"v": 1}},
            {"$sample": {"size": 4}},
            {"$count": "n"},
        ],
        expected=[{"n": 4}],
        msg="$sample should work after a $project stage",
    ),
    StageTestCase(
        "position_multiple_sample_stages",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[
            {"$sample": {"size": 3}},
            {"$sample": {"size": 5}},
            {"$count": "n"},
        ],
        expected=[{"n": 3}],
        msg="$sample followed by $sample should operate on the previous stage's output",
    ),
    StageTestCase(
        "compose_limit",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[{"$limit": 3}, {"$sample": {"size": 5}}, {"$count": "n"}],
        expected=[{"n": 3}],
        msg="$sample after $limit should draw from the limited stream",
    ),
    StageTestCase(
        "compose_skip",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[{"$skip": 7}, {"$sample": {"size": 5}}, {"$count": "n"}],
        expected=[{"n": 3}],
        msg="$sample after $skip should draw from the reduced stream",
    ),
    StageTestCase(
        "compose_sort",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$sample": {"size": 5}},
            {"$count": "n"},
        ],
        expected=[{"n": 5}],
        msg="$sample after $sort should draw from the sorted stream",
    ),
    StageTestCase(
        "compose_group",
        docs=[{"_id": i, "v": i % 3} for i in range(10)],
        pipeline=[
            {"$group": {"_id": "$v"}},
            {"$sample": {"size": 5}},
            {"$count": "n"},
        ],
        expected=[{"n": 3}],
        msg="$sample after $group should draw from the grouped stream",
    ),
    StageTestCase(
        "compose_group_shape",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[
            {"$group": {"_id": None, "n": {"$sum": 1}}},
            {"$sample": {"size": 1}},
            {"$project": {"_id": 0, "n": 1}},
        ],
        expected=[{"n": 10}],
        msg="$sample after $group should preserve grouped document shape",
    ),
    StageTestCase(
        "compose_unwind",
        docs=[{"_id": i, "arr": [1, 2]} for i in range(5)],
        pipeline=[
            {"$unwind": "$arr"},
            {"$sample": {"size": 15}},
            {"$count": "n"},
        ],
        expected=[{"n": 10}],
        msg="$sample after $unwind should draw from the expanded stream",
    ),
    StageTestCase(
        "compose_unwind_shape",
        docs=[{"_id": i, "arr": [1, 2]} for i in range(5)],
        pipeline=[
            {"$unwind": "$arr"},
            {"$sample": {"size": 1}},
            {"$project": {"_id": 0, "arrType": {"$type": "$arr"}}},
        ],
        expected=[{"arrType": "int"}],
        msg="$sample after $unwind should yield a scalar, not an array",
    ),
    StageTestCase(
        "compose_addfields",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[
            {"$addFields": {"extra": 1}},
            {"$sample": {"size": 3}},
            {"$count": "n"},
        ],
        expected=[{"n": 3}],
        msg="$sample after $addFields should draw from the enriched stream",
    ),
    StageTestCase(
        "compose_addfields_shape",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[
            {"$addFields": {"extra": 1}},
            {"$sample": {"size": 1}},
            {"$project": {"_id": 0, "extra": 1}},
        ],
        expected=[{"extra": 1}],
        msg="$sample after $addFields should preserve the added field",
    ),
    StageTestCase(
        "compose_set",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[
            {"$set": {"extra": 1}},
            {"$sample": {"size": 3}},
            {"$count": "n"},
        ],
        expected=[{"n": 3}],
        msg="$sample after $set should draw from the enriched stream",
    ),
    StageTestCase(
        "compose_set_shape",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[
            {"$set": {"extra": 1}},
            {"$sample": {"size": 1}},
            {"$project": {"_id": 0, "extra": 1}},
        ],
        expected=[{"extra": 1}],
        msg="$sample after $set should preserve the set field",
    ),
    StageTestCase(
        "compose_facet",
        docs=[{"_id": i} for i in range(10)],
        pipeline=[
            {
                "$facet": {
                    "sampled": [{"$sample": {"size": 3}}, {"$count": "n"}],
                    "total": [{"$count": "n"}],
                }
            },
        ],
        expected=[{"sampled": [{"n": 3}], "total": [{"n": 10}]}],
        msg="$sample in one $facet arm should not affect other arms",
    ),
    StageTestCase(
        "compose_replaceRoot",
        docs=[{"_id": i, "inner": {"v": i}} for i in range(10)],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$sample": {"size": 3}},
            {"$count": "n"},
        ],
        expected=[{"n": 3}],
        msg="$sample after $replaceRoot should draw from the replaced stream",
    ),
    StageTestCase(
        "compose_replaceRoot_shape",
        docs=[{"_id": i, "inner": {"tag": "replaced"}} for i in range(10)],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$sample": {"size": 1}},
            {"$project": {"_id": 0, "tag": 1}},
        ],
        expected=[{"tag": "replaced"}],
        msg="$sample after $replaceRoot should preserve the replaced shape",
    ),
    StageTestCase(
        "compose_replaceWith",
        docs=[{"_id": i, "inner": {"v": i}} for i in range(10)],
        pipeline=[
            {"$replaceWith": "$inner"},
            {"$sample": {"size": 3}},
            {"$count": "n"},
        ],
        expected=[{"n": 3}],
        msg="$sample after $replaceWith should draw from the replaced stream",
    ),
    StageTestCase(
        "compose_replaceWith_shape",
        docs=[{"_id": i, "inner": {"tag": "replaced"}} for i in range(10)],
        pipeline=[
            {"$replaceWith": "$inner"},
            {"$sample": {"size": 1}},
            {"$project": {"_id": 0, "tag": 1}},
        ],
        expected=[{"tag": "replaced"}],
        msg="$sample after $replaceWith should preserve the replaced shape",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SAMPLE_PIPELINE_COMPOSITION_TESTS))
def test_stages_combination_sample(collection, test_case: StageTestCase):
    """Test $sample composing with other pipeline stages."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


@pytest.mark.aggregate
def test_sample_compose_out(collection):
    """Test $sample composes correctly with $out."""
    collection.insert_many([{"_id": i} for i in range(10)])
    db = collection.database
    out_name = collection.name + "_out"
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$sample": {"size": 3}}, {"$out": out_name}],
            "cursor": {},
        },
    )
    result = execute_command(
        collection,
        {
            "aggregate": out_name,
            "pipeline": [{"$count": "n"}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"n": 3}], msg="$out should contain sampled docs")
    db.drop_collection(out_name)


@pytest.mark.aggregate
def test_sample_compose_lookup_pipeline(collection):
    """Test $sample works inside a $lookup sub-pipeline."""
    db = collection.database
    foreign = collection.name + "_lookup"
    db[foreign].insert_many([{"_id": i} for i in range(6)])
    collection.insert_many([{"_id": 1}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": foreign,
                        "pipeline": [
                            {"$sample": {"size": 2}},
                            {"$count": "n"},
                        ],
                        "as": "looked",
                    }
                },
                {"$project": {"_id": 0, "looked": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"looked": [{"n": 2}]}],
        msg="$sample should work inside a $lookup pipeline",
    )
    db.drop_collection(foreign)


@pytest.mark.aggregate
def test_sample_compose_unionwith(collection):
    """Test $sample works inside a $unionWith sub-pipeline."""
    db = collection.database
    other = collection.name + "_union"
    db[other].insert_many([{"_id": i} for i in range(6)])
    collection.insert_many([{"_id": 1}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$unionWith": {
                        "coll": other,
                        "pipeline": [{"$sample": {"size": 3}}],
                    }
                },
                {"$count": "n"},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"n": 4}],
        msg="$sample should work inside a $unionWith sub-pipeline",
    )
    db.drop_collection(other)


@pytest.mark.aggregate
def test_sample_compose_merge(collection):
    """Test $sample composes correctly with $merge."""
    collection.insert_many([{"_id": i} for i in range(10)])
    db = collection.database
    merge_name = collection.name + "_merge"
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sample": {"size": 3}},
                {"$merge": {"into": merge_name}},
            ],
            "cursor": {},
        },
    )
    result = execute_command(
        collection,
        {
            "aggregate": merge_name,
            "pipeline": [{"$count": "n"}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"n": 3}], msg="$merge should contain sampled docs")
    db.drop_collection(merge_name)
