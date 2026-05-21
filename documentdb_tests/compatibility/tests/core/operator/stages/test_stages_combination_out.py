"""Tests for $out stage — pipeline integration with other stages."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.out.utils.out_test_helpers import (
    OutTestCase,
    target_name,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Integration]: $out composes correctly with other
# aggregation stages — $match filters before writing, $project reshapes
# output, $group aggregates, $sort/$limit/$skip paginate, $unwind expands
# arrays, $addFields enriches, $replaceRoot restructures, $redact prunes,
# $lookup joins, and $unionWith merges collections.
OUT_PIPELINE_INTEGRATION_TESTS: list[OutTestCase] = [
    OutTestCase(
        "match_equality",
        docs=[
            {"_id": 1, "status": "active", "val": 10},
            {"_id": 2, "status": "inactive", "val": 20},
            {"_id": 3, "status": "active", "val": 30},
        ],
        pipeline=[
            {"$match": {"status": "active"}},
        ],
        expected=[
            {"_id": 1, "status": "active", "val": 10},
            {"_id": 3, "status": "active", "val": 30},
        ],
        msg="$out should write only the documents that pass the $match filter",
    ),
    OutTestCase(
        "match_comparison",
        docs=[
            {"_id": 1, "val": 5},
            {"_id": 2, "val": 15},
            {"_id": 3, "val": 25},
        ],
        pipeline=[
            {"$match": {"val": {"$gte": 15}}},
        ],
        expected=[
            {"_id": 2, "val": 15},
            {"_id": 3, "val": 25},
        ],
        msg="$out should write documents matching a comparison $match filter",
    ),
    OutTestCase(
        "match_no_results",
        docs=[
            {"_id": 1, "val": 10},
            {"_id": 2, "val": 20},
        ],
        pipeline=[
            {"$match": {"val": {"$gt": 100}}},
        ],
        expected=[],
        msg="$out should create an empty collection when $match filters all documents",
    ),
    OutTestCase(
        "project_inclusion",
        docs=[
            {"_id": 1, "a": 1, "b": 2, "c": 3},
            {"_id": 2, "a": 4, "b": 5, "c": 6},
        ],
        pipeline=[
            {"$project": {"a": 1, "b": 1}},
        ],
        expected=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 4, "b": 5},
        ],
        msg="$out should write only the fields kept by an inclusion $project",
    ),
    OutTestCase(
        "project_computed",
        docs=[
            {"_id": 1, "x": 10},
            {"_id": 2, "x": 20},
        ],
        pipeline=[
            {"$project": {"doubled": {"$multiply": ["$x", 2]}}},
        ],
        expected=[
            {"_id": 1, "doubled": 20},
            {"_id": 2, "doubled": 40},
        ],
        msg="$out should write computed fields from a $project stage",
    ),
    OutTestCase(
        "group_sum",
        docs=[
            {"_id": 1, "cat": "a", "val": 10},
            {"_id": 2, "cat": "a", "val": 20},
            {"_id": 3, "cat": "b", "val": 30},
        ],
        pipeline=[
            {"$group": {"_id": "$cat", "total": {"$sum": "$val"}}},
        ],
        expected=[
            {"_id": "a", "total": 30},
            {"_id": "b", "total": 30},
        ],
        msg="$out should write $group $sum results to the target collection",
    ),
    OutTestCase(
        "group_count",
        docs=[
            {"_id": 1, "cat": "x"},
            {"_id": 2, "cat": "x"},
            {"_id": 3, "cat": "y"},
        ],
        pipeline=[
            {"$group": {"_id": "$cat", "n": {"$sum": 1}}},
        ],
        expected=[
            {"_id": "x", "n": 2},
            {"_id": "y", "n": 1},
        ],
        msg="$out should write $group count results to the target collection",
    ),
    OutTestCase(
        "sort_limit_top_n",
        docs=[
            {"_id": 1, "val": 50},
            {"_id": 2, "val": 10},
            {"_id": 3, "val": 40},
            {"_id": 4, "val": 30},
            {"_id": 5, "val": 20},
        ],
        pipeline=[
            {"$sort": {"val": -1}},
            {"$limit": 3},
        ],
        expected=[
            {"_id": 1, "val": 50},
            {"_id": 3, "val": 40},
            {"_id": 4, "val": 30},
        ],
        msg="$out should write the top-N sorted documents after $sort and $limit",
    ),
    OutTestCase(
        "skip_limit_page",
        docs=[
            {"_id": 1, "val": 10},
            {"_id": 2, "val": 20},
            {"_id": 3, "val": 30},
            {"_id": 4, "val": 40},
            {"_id": 5, "val": 50},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$skip": 1},
            {"$limit": 2},
        ],
        expected=[
            {"_id": 2, "val": 20},
            {"_id": 3, "val": 30},
        ],
        msg="$out should write the paginated window from $skip and $limit",
    ),
    OutTestCase(
        "unwind_group_tag_count",
        docs=[
            {"_id": 1, "tags": ["a", "b"]},
            {"_id": 2, "tags": ["b", "c"]},
            {"_id": 3, "tags": ["a"]},
        ],
        pipeline=[
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        ],
        expected=[
            {"_id": "a", "count": 2},
            {"_id": "b", "count": 2},
            {"_id": "c", "count": 1},
        ],
        msg="$out should write unwound-then-grouped tag counts to the target collection",
    ),
    OutTestCase(
        "addfields_computed",
        docs=[
            {"_id": 1, "price": 100, "qty": 3},
            {"_id": 2, "price": 200, "qty": 1},
        ],
        pipeline=[
            {"$addFields": {"total": {"$multiply": ["$price", "$qty"]}}},
        ],
        expected=[
            {"_id": 1, "price": 100, "qty": 3, "total": 300},
            {"_id": 2, "price": 200, "qty": 1, "total": 200},
        ],
        msg="$out should write documents enriched by $addFields to the target collection",
    ),
    OutTestCase(
        "replaceroot_nested",
        docs=[
            {"_id": 1, "inner": {"a": 10, "b": 20}},
            {"_id": 2, "inner": {"a": 30, "b": 40}},
        ],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$addFields": {"_id": "$a"}},
        ],
        expected=[
            {"_id": 10, "a": 10, "b": 20},
            {"_id": 30, "a": 30, "b": 40},
        ],
        msg="$out should write the new root structure after $replaceRoot",
    ),
    OutTestCase(
        "redact_keep_prune",
        docs=[
            {"_id": 1, "level": 1, "data": "public"},
            {"_id": 2, "level": 5, "data": "secret"},
            {"_id": 3, "level": 2, "data": "internal"},
        ],
        pipeline=[
            {
                "$redact": {
                    "$cond": {
                        "if": {"$lte": ["$level", 2]},
                        "then": "$$KEEP",
                        "else": "$$PRUNE",
                    }
                }
            },
        ],
        expected=[
            {"_id": 1, "level": 1, "data": "public"},
            {"_id": 3, "level": 2, "data": "internal"},
        ],
        msg="$out should write only documents kept by $redact",
    ),
    OutTestCase(
        "match_group_sort_out",
        docs=[
            {"_id": 1, "dept": "eng", "salary": 100},
            {"_id": 2, "dept": "eng", "salary": 150},
            {"_id": 3, "dept": "sales", "salary": 80},
            {"_id": 4, "dept": "sales", "salary": 120},
            {"_id": 5, "dept": "hr", "salary": 90},
        ],
        pipeline=[
            {"$match": {"salary": {"$gte": 90}}},
            {"$group": {"_id": "$dept", "avg_salary": {"$avg": "$salary"}}},
            {"$sort": {"avg_salary": -1}},
        ],
        expected=[
            {"_id": "eng", "avg_salary": 125.0},
            {"_id": "hr", "avg_salary": 90.0},
            {"_id": "sales", "avg_salary": 120.0},
        ],
        msg="$out should write correctly after $match, $group, and $sort combined",
    ),
    OutTestCase(
        "project_addfields_match_out",
        docs=[
            {"_id": 1, "price": 50, "qty": 4},
            {"_id": 2, "price": 30, "qty": 10},
            {"_id": 3, "price": 20, "qty": 2},
        ],
        pipeline=[
            {"$project": {"price": 1, "qty": 1}},
            {"$addFields": {"revenue": {"$multiply": ["$price", "$qty"]}}},
            {"$match": {"revenue": {"$gte": 200}}},
        ],
        expected=[
            {"_id": 1, "price": 50, "qty": 4, "revenue": 200},
            {"_id": 2, "price": 30, "qty": 10, "revenue": 300},
        ],
        msg="$out should write correctly after $project, $addFields, and $match combined",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_PIPELINE_INTEGRATION_TESTS))
def test_out_pipeline_integration(collection, test_case: OutTestCase):
    """Test $out pipeline integration with other stages."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    db = collection.database
    target = target_name(collection, test_case)
    pipeline = list(test_case.pipeline) + [test_case.build_out_stage(collection)]
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    result = execute_command(
        collection,
        {"find": target, "filter": {}, "sort": {"_id": 1}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
    db.drop_collection(target)


@pytest.mark.aggregate
def test_out_lookup_equality(collection):
    """Test $out after $lookup with equality join."""
    db = collection.database
    foreign_name = f"{collection.name}_integration_foreign"
    out_name = f"{collection.name}_integration_out"
    collection.insert_many([{"_id": 1, "ref": 1}, {"_id": 2, "ref": 2}])
    db[foreign_name].insert_many([{"_id": 1, "label": "first"}, {"_id": 2, "label": "second"}])
    pipeline = [
        {
            "$lookup": {
                "from": foreign_name,
                "localField": "ref",
                "foreignField": "_id",
                "as": "joined",
            }
        },
        {"$project": {"ref": 1, "label": {"$arrayElemAt": ["$joined.label", 0]}}},
        {"$out": out_name},
    ]
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    result = execute_command(
        collection,
        {"find": out_name, "filter": {}, "sort": {"_id": 1}},
    )
    assertResult(
        result,
        expected=[
            {"_id": 1, "ref": 1, "label": "first"},
            {"_id": 2, "ref": 2, "label": "second"},
        ],
        msg="$out should write $lookup-joined documents to the target collection",
    )
    db.drop_collection(out_name)
    db.drop_collection(foreign_name)


@pytest.mark.aggregate
def test_out_unionwith_merge(collection):
    """Test $out after $unionWith merging two collections."""
    db = collection.database
    foreign_name = f"{collection.name}_integration_foreign"
    out_name = f"{collection.name}_integration_out"
    collection.insert_many([{"_id": 1, "source": "main"}, {"_id": 2, "source": "main"}])
    db[foreign_name].insert_many([{"_id": 3, "source": "other"}, {"_id": 4, "source": "other"}])
    pipeline = [
        {"$unionWith": {"coll": foreign_name}},
        {"$out": out_name},
    ]
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    result = execute_command(
        collection,
        {"find": out_name, "filter": {}, "sort": {"_id": 1}},
    )
    assertResult(
        result,
        expected=[
            {"_id": 1, "source": "main"},
            {"_id": 2, "source": "main"},
            {"_id": 3, "source": "other"},
            {"_id": 4, "source": "other"},
        ],
        msg="$out should write $unionWith-merged documents to the target collection",
    )
    db.drop_collection(out_name)
    db.drop_collection(foreign_name)
