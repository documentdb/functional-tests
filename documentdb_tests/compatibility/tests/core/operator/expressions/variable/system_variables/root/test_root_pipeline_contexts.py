"""
Pipeline stage context tests for the $$ROOT system variable.

Covers $$ROOT as the document flowing through an aggregation pipeline
(reshaped by preceding stages, $group accumulator agreement with $$CURRENT,
dollar-prefixed DBRef fields) and outside the aggregate command (find()'s
$expr, update-with-pipeline, findAndModify's computed projection).

$lookup rebinding, $replaceRoot's own contract, and $setField's input handling
are delegated to their own folders. $facet and find() projections are
§11-exempt.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOC_ONE = {"_id": 1, "a": 1, "b": "keep", "arr": [7, 8]}
DOC_TWO = {"_id": 2, "a": 2, "b": "drop", "arr": [9]}


# Property [Current Pipeline Document]: $$ROOT is the document entering the current
# stage — the output of all preceding stages, not the stored document — so it reflects
# projections, added fields, group output, promoted roots, and unwound elements, and can
# itself be reshaped by operators into a new root.
PIPELINE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="after_project_sees_only_surviving_fields",
        docs=[DOC_ONE, DOC_TWO],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$project": {"a": 1}},
            {"$addFields": {"snap": "$$ROOT"}},
        ],
        expected=[
            {"_id": 1, "a": 1, "snap": {"_id": 1, "a": 1}},
            {"_id": 2, "a": 2, "snap": {"_id": 2, "a": 2}},
        ],
        msg="$$ROOT should reflect the projected document, not the stored document",
    ),
    StageTestCase(
        id="after_add_fields_includes_new_field",
        docs=[DOC_ONE],
        pipeline=[{"$addFields": {"n": 99}}, {"$project": {"_id": 0, "snap": "$$ROOT"}}],
        expected=[{"snap": {**DOC_ONE, "n": 99}}],
        msg="$$ROOT should include fields added by $addFields",
    ),
    StageTestCase(
        id="after_group_is_the_group_output",
        docs=[DOC_ONE, DOC_TWO],
        pipeline=[
            {"$group": {"_id": None, "total": {"$sum": "$a"}}},
            {"$project": {"_id": 0, "snap": "$$ROOT"}},
        ],
        expected=[{"snap": {"_id": None, "total": 3}}],
        msg="$$ROOT should be the group output document after $group",
    ),
    StageTestCase(
        id="after_replace_root_is_the_promoted_document",
        docs=[DOC_ONE, DOC_TWO],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$replaceRoot": {"newRoot": {"inner": "$$ROOT"}}},
            {"$project": {"_id": 0, "snap": "$$ROOT.inner.a"}},
        ],
        expected=[{"snap": 1}, {"snap": 2}],
        msg="$$ROOT should be the promoted document after $replaceRoot",
    ),
    StageTestCase(
        id="after_unwind_holds_single_array_element",
        docs=[DOC_ONE],
        pipeline=[{"$unwind": "$arr"}, {"$project": {"_id": 0, "snap": "$$ROOT"}}],
        expected=[
            {"snap": {"_id": 1, "a": 1, "b": "keep", "arr": 7}},
            {"snap": {"_id": 1, "a": 1, "b": "keep", "arr": 8}},
        ],
        msg="$$ROOT after $unwind should hold a single unwound array element",
    ),
    StageTestCase(
        id="field_access_matches_current_in_group_accumulator",
        docs=[{"_id": 1, "a": 99}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "viaField": {"$first": "$a"},
                    "viaCurrent": {"$first": "$$CURRENT.a"},
                    "viaRoot": {"$first": "$$ROOT.a"},
                }
            },
            {"$project": {"_id": 0}},
        ],
        expected=[{"viaField": 99, "viaCurrent": 99, "viaRoot": 99}],
        msg="The three field path forms should agree inside a $group accumulator",
    ),
    StageTestCase(
        id="reaches_top_level_dbref_field",
        docs=[{"_id": 1, "link": {"$ref": "otherColl", "$id": "id0"}}],
        pipeline=[
            {"$project": {"$ref": "$link.$ref"}},
            {"$project": {"_id": 0, "x": "$$ROOT.$ref"}},
        ],
        expected=[{"x": "otherColl"}],
        msg="$$ROOT should reach a top-level dollar-prefixed DBRef field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PIPELINE_TESTS))
def test_root_in_pipeline_context(collection, test: StageTestCase):
    """$$ROOT resolves against the document flowing through an aggregation pipeline."""
    populate_collection(collection, test)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test.pipeline, "cursor": {}},
    )
    assertSuccess(result, test.expected, msg=test.msg)


def test_root_in_lookup_subpipeline(collection):
    """$$ROOT inside a $lookup sub-pipeline rebinds to the foreign document."""
    foreign = collection.database["root_pipeline_contexts_foreign"]
    foreign.drop()
    foreign.insert_one({"_id": 10, "a": 1, "tag": "foreign"})
    collection.insert_one({"_id": 1, "a": 1, "tag": "outer"})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": foreign.name,
                        "let": {"outerVal": "$$ROOT.a"},
                        "pipeline": [
                            {
                                "$project": {
                                    "_id": 0,
                                    "innerRoot": "$$ROOT",
                                    "outerViaLet": "$$outerVal",
                                }
                            }
                        ],
                        "as": "joined",
                    }
                },
                {"$project": {"_id": 0, "joined": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"joined": [{"innerRoot": {"_id": 10, "a": 1, "tag": "foreign"}, "outerViaLet": 1}]}],
        msg=(
            "$$ROOT inside a $lookup sub-pipeline should rebind to the foreign document, "
            "while the outer value stays reachable only through 'let'"
        ),
    )


def test_root_in_find_expr_filter(collection):
    """$$ROOT inside a find() filter's $expr matches against the whole candidate document."""
    collection.insert_many([{"_id": 1, "a": 1, "b": 1}, {"_id": 2, "a": 1, "b": 2}])

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$eq": ["$$ROOT.a", "$$ROOT.b"]}},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "a": 1, "b": 1}],
        msg="find's $expr filter should evaluate $$ROOT against each candidate document",
    )


def test_root_in_update_pipeline(collection):
    """$$ROOT inside an update-with-pipeline stage snapshots the pre-update document."""
    collection.insert_one({"_id": 1, "a": 1, "b": 2})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": [{"$set": {"snapshot": "$$ROOT", "a": 99}}],
                }
            ],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "a": 99, "b": 2, "snapshot": {"_id": 1, "a": 1, "b": 2}}],
        msg="$$ROOT in an update pipeline should snapshot the document as it was before the update",
    )


def test_root_in_findAndModify_projection(collection):
    """$$ROOT in findAndModify's computed 'fields' projection captures the returned image."""
    collection.insert_one({"_id": 1, "x": 5})

    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$set": {"x": 10}},
            "fields": {"snapshot": "$$ROOT", "_id": 0},
            "new": True,
        },
    )
    assertSuccess(
        result,
        {
            "lastErrorObject": {"n": 1, "updatedExisting": True},
            "value": {"snapshot": {"_id": 1, "x": 10}},
            "ok": 1.0,
        },
        msg="$$ROOT in findAndModify's computed projection should resolve to the post-image "
        "document when new:true",
        raw_res=True,
    )
