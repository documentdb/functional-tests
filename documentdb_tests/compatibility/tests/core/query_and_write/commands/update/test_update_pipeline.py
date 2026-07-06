"""
Tests for update command with aggregation pipeline mode.

Validates pipeline updates with $set, $unset, $replaceWith, $replaceRoot,
disallowed stages, and pipeline with expressions.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR
from documentdb_tests.framework.executor import execute_command


def test_update_pipeline_set_adds_field(collection):
    """Test pipeline update with $set stage adds new field."""
    collection.insert_one({"_id": 1, "x": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": [{"$set": {"y": 2}}]}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "x": 1, "y": 2}])


def test_update_pipeline_unset_removes_field(collection):
    """Test pipeline update with $unset stage removes specified fields."""
    collection.insert_one({"_id": 1, "a": 1, "b": 2, "c": 3})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": [{"$unset": ["b", "c"]}]}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "a": 1}])


def test_update_pipeline_replaceWith(collection):
    """Test pipeline update with $replaceWith stage replaces document."""
    collection.insert_one({"_id": 1, "x": 1, "nested": {"a": 10, "b": 20}})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": [{"$replaceWith": "$nested"}]}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "a": 10, "b": 20}])


def test_update_pipeline_project_removes_fields(collection):
    """Test pipeline update with $project stage removes unspecified fields."""
    collection.insert_one({"_id": 1, "a": 1, "b": 2, "c": 3})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": [{"$project": {"a": 1}}]}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "a": 1}])


def test_update_pipeline_multi_true(collection):
    """Test pipeline update with multi:true applies to all matching docs."""
    collection.insert_many(
        [
            {"_id": 1, "s": "A", "v": 1},
            {"_id": 2, "s": "A", "v": 2},
            {"_id": 3, "s": "B", "v": 3},
        ]
    )
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"s": "A"}, "u": [{"$set": {"updated": True}}], "multi": True}],
        },
    )
    assertSuccess(result, {"ok": 1.0, "n": 2, "nModified": 2}, raw_res=True)


def test_update_pipeline_multiple_stages(collection):
    """Test pipeline with multiple stages in sequence."""
    collection.insert_one({"_id": 1, "a": 1, "b": 2})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": [
                        {"$set": {"c": {"$add": ["$a", "$b"]}}},
                        {"$unset": ["a", "b"]},
                    ],
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "c": 3}])


def test_update_pipeline_empty_array_no_change(collection):
    """Test empty pipeline [] makes no change to document."""
    collection.insert_one({"_id": 1, "x": 5})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": []}],
        },
    )
    assertSuccess(result, {"ok": 1.0, "n": 1, "nModified": 0}, raw_res=True)


# Only $addFields/$set, $project/$unset, and $replaceRoot/$replaceWith are
# allowed in pipeline updates. Every other stage is rejected with
# INVALID_OPTIONS_ERROR. Stages with required fields are given minimal valid
# arguments to ensure the rejection is for "not allowed", not "missing field".
_DISALLOWED_STAGE_PARAMS = [
    pytest.param({"$group": {"_id": "$x"}}, id="group"),
    pytest.param({"$match": {"x": 1}}, id="match"),
    pytest.param({"$sort": {"x": 1}}, id="sort"),
    pytest.param(
        {"$lookup": {"from": "other", "localField": "x", "foreignField": "x", "as": "r"}},
        id="lookup",
    ),
    pytest.param({"$out": "other"}, id="out"),
    pytest.param({"$merge": {"into": "other"}}, id="merge"),
    pytest.param({"$facet": {"a": [{"$count": "n"}]}}, id="facet"),
    pytest.param({"$unionWith": {"coll": "other"}}, id="unionWith"),
    pytest.param({"$geoNear": {"near": [0, 0], "distanceField": "d"}}, id="geoNear"),
    pytest.param(
        {
            "$graphLookup": {
                "from": "other",
                "startWith": "$x",
                "connectFromField": "x",
                "connectToField": "x",
                "as": "r",
            }
        },
        id="graphLookup",
    ),
    pytest.param({"$bucket": {"groupBy": "$x", "boundaries": [0, 10]}}, id="bucket"),
]


@pytest.mark.parametrize("stage", _DISALLOWED_STAGE_PARAMS)
def test_update_pipeline_disallowed_stage(collection, stage):
    """Test pipeline update rejects stages not in the allowed set."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": [stage]}],
        },
    )
    assertFailureCode(result, INVALID_OPTIONS_ERROR)


def test_update_pipeline_with_cond_expression(collection):
    """Test pipeline with $cond conditional logic."""
    collection.insert_many(
        [
            {"_id": 1, "score": 80},
            {"_id": 2, "score": 40},
        ]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {},
                    "u": [
                        {
                            "$set": {
                                "grade": {
                                    "$cond": {
                                        "if": {"$gte": ["$score", 60]},
                                        "then": "pass",
                                        "else": "fail",
                                    }
                                }
                            }
                        }
                    ],
                    "multi": True,
                }
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {}, "sort": {"_id": 1}},
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "score": 80, "grade": "pass"},
            {"_id": 2, "score": 40, "grade": "fail"},
        ],
    )


def test_update_pipeline_upsert_with_set(collection):
    """Test pipeline upsert with $set inserts doc from query fields with pipeline applied."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": [{"$set": {"status": "new"}}],
                    "upsert": True,
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "status": "new"}])
