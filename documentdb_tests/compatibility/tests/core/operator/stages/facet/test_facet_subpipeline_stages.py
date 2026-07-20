"""Aggregation $facet stage tests - sub-pipeline stage support.

Verifies that a variety of aggregation stages work inside $facet sub-pipelines
and produce the expected output arrays. Per the container-features rule
(FOLDER_STRUCTURE.md), these are one-case-per-sub-feature smoke tests, not
exhaustive edge-case coverage of each inner stage. Also covers JS-derived
use-case scenarios (stages.js, use_cases.js).
"""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len

DOCS = [
    {"_id": 1, "cat": "A", "price": 10, "tags": ["x", "y"]},
    {"_id": 2, "cat": "A", "price": 20, "tags": ["y"]},
    {"_id": 3, "cat": "B", "price": 30, "tags": ["z"]},
    {"_id": 4, "cat": "C", "price": 40, "tags": []},
]

# Property [Sub-Pipeline Stage Support]: common aggregation stages and
# use-case combinations produce the expected output arrays inside $facet.
FACET_SUBPIPELINE_STAGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="sortByCount",
        docs=DOCS,
        pipeline=[{"$facet": {"byCat": [{"$sortByCount": "$cat"}], "total": [{"$count": "n"}]}}],
        expected=[
            {
                "byCat": [
                    {"_id": "A", "count": 2},
                    {"_id": "B", "count": 1},
                    {"_id": "C", "count": 1},
                ],
                "total": [{"n": 4}],
            }
        ],
        msg="$sortByCount sub-pipeline should return {_id, count} documents sorted by count",
        ignore_order_in=["byCat"],
    ),
    StageTestCase(
        id="bucket",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "buckets": [{"$bucket": {"groupBy": "$price", "boundaries": [0, 25, 50]}}],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[
            {"buckets": [{"_id": 0, "count": 2}, {"_id": 25, "count": 2}], "total": [{"n": 4}]}
        ],
        msg="$bucket sub-pipeline should return bucket documents",
    ),
    StageTestCase(
        id="bucketAuto",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "auto": [{"$bucketAuto": {"groupBy": "$price", "buckets": 2}}],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[
            {
                "auto": [
                    {"_id": {"min": 10, "max": 30}, "count": 2},
                    {"_id": {"min": 30, "max": 40}, "count": 2},
                ],
                "total": [{"n": 4}],
            }
        ],
        msg="$bucketAuto sub-pipeline should return auto-bucket documents",
    ),
    StageTestCase(
        id="match_count",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "nA": [{"$match": {"cat": "A"}}, {"$count": "n"}],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[{"nA": [{"n": 2}], "total": [{"n": 4}]}],
        msg="$match + $count sub-pipeline should return a single count document",
    ),
    StageTestCase(
        id="group_sort",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "totals": [
                        {"$group": {"_id": "$cat", "total": {"$sum": "$price"}}},
                        {"$sort": {"_id": 1}},
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[
            {
                "totals": [
                    {"_id": "A", "total": 30},
                    {"_id": "B", "total": 30},
                    {"_id": "C", "total": 40},
                ],
                "total": [{"n": 4}],
            }
        ],
        msg="$group + $sort sub-pipeline should return sorted grouped results",
    ),
    StageTestCase(
        id="limit",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "first2": [{"$sort": {"_id": 1}}, {"$limit": 2}],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[{"first2": [DOCS[0], DOCS[1]], "total": [{"n": 4}]}],
        msg="$limit sub-pipeline should return at most N documents",
    ),
    StageTestCase(
        id="skip",
        docs=DOCS,
        pipeline=[
            {"$facet": {"rest": [{"$sort": {"_id": 1}}, {"$skip": 2}], "total": [{"$count": "n"}]}}
        ],
        expected=[{"rest": [DOCS[2], DOCS[3]], "total": [{"n": 4}]}],
        msg="$skip sub-pipeline should skip the specified number of documents",
    ),
    StageTestCase(
        id="project",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "proj": [{"$sort": {"_id": 1}}, {"$project": {"_id": 0, "cat": 1}}],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[
            {"proj": [{"cat": "A"}, {"cat": "A"}, {"cat": "B"}, {"cat": "C"}], "total": [{"n": 4}]}
        ],
        msg="$project sub-pipeline should return only projected fields",
    ),
    StageTestCase(
        id="unwind",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "unwound": [
                        {"$match": {"_id": 1}},
                        {"$unwind": "$tags"},
                        {"$project": {"_id": 1, "tags": 1}},
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[
            {"unwound": [{"_id": 1, "tags": "x"}, {"_id": 1, "tags": "y"}], "total": [{"n": 4}]}
        ],
        msg="$unwind sub-pipeline should return unwound documents",
    ),
    StageTestCase(
        id="addFields",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "withDouble": [
                        {"$match": {"_id": 1}},
                        {"$addFields": {"double": {"$multiply": ["$price", 2]}}},
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[
            {
                "withDouble": [
                    {"_id": 1, "cat": "A", "price": 10, "tags": ["x", "y"], "double": 20}
                ],
                "total": [{"n": 4}],
            }
        ],
        msg="$addFields sub-pipeline should add a computed field",
    ),
    StageTestCase(
        id="replaceRoot",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "replaced": [
                        {"$match": {"_id": 1}},
                        {"$replaceRoot": {"newRoot": {"only": "$cat"}}},
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[{"replaced": [{"only": "A"}], "total": [{"n": 4}]}],
        msg="$replaceRoot sub-pipeline should replace the document root",
    ),
    StageTestCase(
        id="multiple_chained_stages",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "chain": [
                        {"$match": {"cat": "A"}},
                        {"$group": {"_id": None, "total": {"$sum": "$price"}}},
                        {"$project": {"_id": 0, "total": 1}},
                    ],
                    "n": [{"$count": "n"}],
                }
            }
        ],
        expected=[{"chain": [{"total": 30}], "n": [{"n": 4}]}],
        msg="A chained sub-pipeline should return the result of the full chain",
    ),
    StageTestCase(
        id="two_group_subpipelines",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "byCat": [
                        {"$group": {"_id": "$cat", "sum": {"$sum": "$price"}}},
                        {"$sort": {"_id": 1}},
                    ],
                    "byId": [
                        {"$group": {"_id": "$_id", "sum": {"$sum": "$price"}}},
                        {"$sort": {"_id": 1}},
                    ],
                }
            }
        ],
        expected=[
            {
                "byCat": [
                    {"_id": "A", "sum": 30},
                    {"_id": "B", "sum": 30},
                    {"_id": "C", "sum": 40},
                ],
                "byId": [
                    {"_id": 1, "sum": 10},
                    {"_id": 2, "sum": 20},
                    {"_id": 3, "sum": 30},
                    {"_id": 4, "sum": 40},
                ],
            }
        ],
        msg="Two $group sub-pipelines should each return their own grouped results",
    ),
    StageTestCase(
        id="multi_subpipeline_use_case",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "byCat": [{"$sortByCount": "$cat"}, {"$sort": {"count": -1, "_id": 1}}],
                    "priceBuckets": [
                        {
                            "$bucket": {
                                "groupBy": "$price",
                                "boundaries": [0, 25, 50],
                                "default": "other",
                            }
                        }
                    ],
                    "autoBuckets": [{"$bucketAuto": {"groupBy": "$price", "buckets": 2}}],
                }
            }
        ],
        expected=[
            {
                "byCat": [
                    {"_id": "A", "count": 2},
                    {"_id": "B", "count": 1},
                    {"_id": "C", "count": 1},
                ],
                "priceBuckets": [{"_id": 0, "count": 2}, {"_id": 25, "count": 2}],
                "autoBuckets": [
                    {"_id": {"min": 10, "max": 30}, "count": 2},
                    {"_id": {"min": 30, "max": 40}, "count": 2},
                ],
            }
        ],
        msg="Multi-sub-pipeline use case should return three independent result arrays",
    ),
    StageTestCase(
        id="match_dotted_array_path_count",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "withY": [{"$match": {"tags": "y"}}, {"$count": "n"}],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[{"withY": [{"n": 2}], "total": [{"n": 4}]}],
        msg="$match on an array field + $count should count matching documents",
    ),
    StageTestCase(
        id="nonexistent_field_no_crash",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "byMissing": [{"$sortByCount": "$doesNotExist"}],
                    "autoMissing": [{"$bucketAuto": {"groupBy": "$doesNotExist", "buckets": 1}}],
                }
            }
        ],
        expected={
            "byMissing": Eq([{"_id": None, "count": 4}]),
            "autoMissing": [Len(1), Eq([{"_id": {"min": None, "max": None}, "count": 4}])],
        },
        msg="Sub-pipelines on a non-existent field should not crash and return one doc each",
    ),
    StageTestCase(
        id="redact",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "filtered": [
                        {
                            "$redact": {
                                "$cond": {
                                    "if": {"$eq": ["$cat", "A"]},
                                    "then": "$$KEEP",
                                    "else": "$$PRUNE",
                                }
                            }
                        },
                        {"$sort": {"_id": 1}},
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[
            {
                "filtered": [
                    {"_id": 1, "cat": "A", "price": 10, "tags": ["x", "y"]},
                    {"_id": 2, "cat": "A", "price": 20, "tags": ["y"]},
                ],
                "total": [{"n": 4}],
            }
        ],
        msg="$redact sub-pipeline should prune documents not matching the condition",
    ),
    StageTestCase(
        id="sample",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "picked": [{"$sample": {"size": 2}}],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected={"picked": Len(2), "total": Eq([{"n": 4}])},
        msg="$sample sub-pipeline should return exactly the requested number of documents",
    ),
    StageTestCase(
        id="setWindowFields",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "windowed": [
                        {"$sort": {"_id": 1}},
                        {
                            "$setWindowFields": {
                                "sortBy": {"_id": 1},
                                "output": {
                                    "running": {
                                        "$sum": "$price",
                                        "window": {"documents": ["unbounded", "current"]},
                                    }
                                },
                            }
                        },
                        {"$project": {"_id": 1, "running": 1}},
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[
            {
                "windowed": [
                    {"_id": 1, "running": 10},
                    {"_id": 2, "running": 30},
                    {"_id": 3, "running": 60},
                    {"_id": 4, "running": 100},
                ],
                "total": [{"n": 4}],
            }
        ],
        msg="$setWindowFields sub-pipeline should compute a running total over sorted documents",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(FACET_SUBPIPELINE_STAGE_TESTS))
def test_facet_subpipeline_stages(collection, test_case: StageTestCase):
    """Test that common stages work correctly inside $facet sub-pipelines."""
    coll = populate_collection(collection, test_case)
    command: dict[str, Any] = {
        "aggregate": coll.name,
        "pipeline": test_case.pipeline,
        "cursor": {},
    }
    command.update(test_case.extra_command_fields)
    result = execute_command(coll, command)
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=test_case.ignore_doc_order,
        ignore_order_in=test_case.ignore_order_in,
    )


@pytest.mark.aggregate
def test_facet_subpipeline_lookup_basic(collection):
    """A simple equi-join $lookup inside a $facet sub-pipeline returns joined results."""
    collection.insert_many([{"_id": 1, "lf": "a"}, {"_id": 2, "lf": "b"}])
    foreign = f"{collection.name}_foreign"
    db = collection.database
    db[foreign].insert_many([{"_id": 10, "ff": "a"}, {"_id": 11, "ff": "b"}])
    try:
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {
                        "$facet": {
                            "joined": [
                                {
                                    "$lookup": {
                                        "from": foreign,
                                        "localField": "lf",
                                        "foreignField": "ff",
                                        "as": "j",
                                    }
                                },
                                {"$sort": {"_id": 1}},
                            ]
                        }
                    }
                ],
                "cursor": {},
            },
        )
        assertSuccess(
            result,
            [
                {
                    "joined": [
                        {"_id": 1, "lf": "a", "j": [{"_id": 10, "ff": "a"}]},
                        {"_id": 2, "lf": "b", "j": [{"_id": 11, "ff": "b"}]},
                    ]
                }
            ],
            msg="Equi-join $lookup inside $facet should return joined arrays",
        )
    finally:
        db.drop_collection(foreign)


@pytest.mark.aggregate
def test_facet_subpipeline_lookup_pipeline_match_project_sort(collection):
    """Pipeline-form $lookup with $match + $project + $sort inside a $facet sub-pipeline."""
    collection.insert_many([{"_id": 1, "key": "a"}, {"_id": 2, "key": "b"}])
    foreign = f"{collection.name}_foreign"
    db = collection.database
    db[foreign].insert_many(
        [
            {"_id": 10, "fk": "a", "price": 15},
            {"_id": 11, "fk": "a", "price": 5},
            {"_id": 12, "fk": "b", "price": 25},
        ]
    )
    try:
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {
                        "$facet": {
                            "joined": [
                                {"$sort": {"_id": 1}},
                                {
                                    "$lookup": {
                                        "from": foreign,
                                        "let": {"k": "$key"},
                                        "pipeline": [
                                            {"$match": {"$expr": {"$eq": ["$fk", "$$k"]}}},
                                            {"$project": {"_id": 0, "price": 1}},
                                            {"$sort": {"price": 1}},
                                        ],
                                        "as": "matches",
                                    }
                                },
                            ],
                            "total": [{"$count": "n"}],
                        }
                    }
                ],
                "cursor": {},
            },
        )
        assertSuccess(
            result,
            [
                {
                    "joined": [
                        {"_id": 1, "key": "a", "matches": [{"price": 5}, {"price": 15}]},
                        {"_id": 2, "key": "b", "matches": [{"price": 25}]},
                    ],
                    "total": [{"n": 2}],
                }
            ],
            msg="$lookup + $match + $project + $sort should return projected, sorted foreign docs",
        )
    finally:
        db.drop_collection(foreign)


@pytest.mark.aggregate
def test_facet_subpipeline_lookup_pipeline_match_group(collection):
    """$lookup pipeline with $match + $group inside $facet aggregates foreign docs."""
    collection.insert_many([{"_id": 1, "key": "a"}, {"_id": 2, "key": "b"}])
    foreign = f"{collection.name}_foreign"
    db = collection.database
    db[foreign].insert_many(
        [
            {"_id": 10, "fk": "a", "price": 5},
            {"_id": 11, "fk": "a", "price": 15},
            {"_id": 12, "fk": "b", "price": 25},
        ]
    )
    try:
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {
                        "$facet": {
                            "summary": [
                                {"$sort": {"_id": 1}},
                                {
                                    "$lookup": {
                                        "from": foreign,
                                        "let": {"k": "$key"},
                                        "pipeline": [
                                            {"$match": {"$expr": {"$eq": ["$fk", "$$k"]}}},
                                            {"$group": {"_id": None, "total": {"$sum": "$price"}}},
                                        ],
                                        "as": "agg",
                                    }
                                },
                                {
                                    "$project": {
                                        "_id": 1,
                                        "total": {"$arrayElemAt": ["$agg.total", 0]},
                                    }
                                },
                            ],
                            "total": [{"$count": "n"}],
                        }
                    }
                ],
                "cursor": {},
            },
        )
        assertSuccess(
            result,
            [
                {
                    "summary": [
                        {"_id": 1, "total": 20},
                        {"_id": 2, "total": 25},
                    ],
                    "total": [{"n": 2}],
                }
            ],
            msg="$lookup + $match + $group should aggregate foreign docs per joined key",
        )
    finally:
        db.drop_collection(foreign)


@pytest.mark.aggregate
def test_facet_subpipeline_lookup_pipeline_match_addfields_project(collection):
    """Pipeline-form $lookup with $match + $addFields + $project inside a $facet sub-pipeline."""
    collection.insert_many([{"_id": 1, "key": "a"}, {"_id": 2, "key": "b"}])
    foreign = f"{collection.name}_foreign"
    db = collection.database
    db[foreign].insert_many(
        [
            {"_id": 10, "fk": "a", "price": 5, "qty": 2},
            {"_id": 11, "fk": "b", "price": 25, "qty": 3},
        ]
    )
    try:
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {
                        "$facet": {
                            "enriched": [
                                {"$sort": {"_id": 1}},
                                {
                                    "$lookup": {
                                        "from": foreign,
                                        "let": {"k": "$key"},
                                        "pipeline": [
                                            {"$match": {"$expr": {"$eq": ["$fk", "$$k"]}}},
                                            {
                                                "$addFields": {
                                                    "line_total": {"$multiply": ["$price", "$qty"]}
                                                }
                                            },
                                            {"$project": {"_id": 0, "line_total": 1}},
                                        ],
                                        "as": "items",
                                    }
                                },
                            ],
                            "total": [{"$count": "n"}],
                        }
                    }
                ],
                "cursor": {},
            },
        )
        assertSuccess(
            result,
            [
                {
                    "enriched": [
                        {"_id": 1, "key": "a", "items": [{"line_total": 10}]},
                        {"_id": 2, "key": "b", "items": [{"line_total": 75}]},
                    ],
                    "total": [{"n": 2}],
                }
            ],
            msg="$lookup + $match + $addFields + $project should compute derived fields per doc",
        )
    finally:
        db.drop_collection(foreign)


@pytest.mark.aggregate
def test_facet_subpipeline_lookup_pipeline_match_unwind_project_sort(collection):
    """$lookup pipeline with $match + $unwind + $project + $sort inside a $facet pipeline."""
    collection.insert_many([{"_id": 1, "key": "a"}, {"_id": 2, "key": "b"}])
    foreign = f"{collection.name}_foreign"
    db = collection.database
    db[foreign].insert_many(
        [
            {"_id": 10, "fk": "a", "tags": ["x", "y"]},
            {"_id": 11, "fk": "a", "tags": ["z"]},
            {"_id": 12, "fk": "b", "tags": ["w"]},
        ]
    )
    try:
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {
                        "$facet": {
                            "flat": [
                                {"$sort": {"_id": 1}},
                                {
                                    "$lookup": {
                                        "from": foreign,
                                        "let": {"k": "$key"},
                                        "pipeline": [
                                            {"$match": {"$expr": {"$eq": ["$fk", "$$k"]}}},
                                            {"$unwind": "$tags"},
                                            {"$project": {"_id": 0, "tag": "$tags"}},
                                            {"$sort": {"tag": 1}},
                                        ],
                                        "as": "tags",
                                    }
                                },
                            ],
                            "total": [{"$count": "n"}],
                        }
                    }
                ],
                "cursor": {},
            },
        )
        assertSuccess(
            result,
            [
                {
                    "flat": [
                        {"_id": 1, "key": "a", "tags": [{"tag": "x"}, {"tag": "y"}, {"tag": "z"}]},
                        {"_id": 2, "key": "b", "tags": [{"tag": "w"}]},
                    ],
                    "total": [{"n": 2}],
                }
            ],
            msg="$lookup + $match + $unwind + $sort should flatten and sort foreign tag arrays",
        )
    finally:
        db.drop_collection(foreign)


@pytest.mark.aggregate
def test_facet_subpipeline_graphlookup_basic(collection):
    """A $graphLookup inside a $facet sub-pipeline returns the traversal."""
    collection.insert_many(
        [
            {"_id": 1, "name": "a", "reportsTo": None},
            {"_id": 2, "name": "b", "reportsTo": "a"},
            {"_id": 3, "name": "c", "reportsTo": "b"},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$facet": {
                        "graph": [
                            {"$match": {"_id": 3}},
                            {
                                "$graphLookup": {
                                    "from": collection.name,
                                    "startWith": "$reportsTo",
                                    "connectFromField": "reportsTo",
                                    "connectToField": "name",
                                    "as": "chain",
                                }
                            },
                            {
                                "$project": {
                                    "_id": 1,
                                    "chainNames": {
                                        "$sortArray": {
                                            "input": "$chain.name",
                                            "sortBy": 1,
                                        }
                                    },
                                }
                            },
                        ]
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"graph": [{"_id": 3, "chainNames": ["a", "b"]}]}],
        msg="$graphLookup inside $facet should return the traversal chain",
    )


@pytest.mark.aggregate
def test_facet_subpipeline_union_with(collection):
    """$unionWith inside a $facet sub-pipeline combines documents from two pipeline branches."""
    collection.insert_many(
        [
            {"_id": 1, "cat": "A", "price": 10, "tags": ["x", "y"]},
            {"_id": 2, "cat": "A", "price": 20, "tags": ["y"]},
            {"_id": 3, "cat": "B", "price": 30, "tags": ["z"]},
            {"_id": 4, "cat": "C", "price": 40, "tags": []},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$facet": {
                        "union": [
                            {"$match": {"_id": 1}},
                            {
                                "$unionWith": {
                                    "coll": collection.name,
                                    "pipeline": [{"$match": {"_id": 2}}],
                                }
                            },
                            {"$sort": {"_id": 1}},
                        ],
                        "total": [{"$count": "n"}],
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {
                "union": [
                    {"_id": 1, "cat": "A", "price": 10, "tags": ["x", "y"]},
                    {"_id": 2, "cat": "A", "price": 20, "tags": ["y"]},
                ],
                "total": [{"n": 4}],
            }
        ],
        msg="$unionWith sub-pipeline should combine documents from two branches",
    )
