"""Tests that $lookup sub-pipeline stages recognize and resolve let variables."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Sub-Pipeline Let Wiring]: a let variable is recognized and resolved
# inside each supported sub-pipeline stage, evaluated against the outer document.
LOOKUP_VERBOSE_LET_WIRING_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "match_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}, {"_id": 11, "type": "B"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$type", "$$v"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "cat": "A", "joined": [{"_id": 10, "type": "A"}]}],
        msg="$lookup sub-pipeline $match should resolve a let variable in $expr",
    ),
    LookupTestCase(
        "add_fields_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}, {"_id": 11, "type": "B"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [{"$addFields": {"lv": "$$v"}}, {"$sort": {"_id": 1}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "cat": "A",
                "joined": [
                    {"_id": 10, "type": "A", "lv": "A"},
                    {"_id": 11, "type": "B", "lv": "A"},
                ],
            }
        ],
        msg="$lookup sub-pipeline $addFields should resolve a let variable",
    ),
    LookupTestCase(
        "set_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}, {"_id": 11, "type": "B"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [{"$set": {"lv": "$$v"}}, {"$sort": {"_id": 1}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "cat": "A",
                "joined": [
                    {"_id": 10, "type": "A", "lv": "A"},
                    {"_id": 11, "type": "B", "lv": "A"},
                ],
            }
        ],
        msg="$lookup sub-pipeline $set should resolve a let variable",
    ),
    LookupTestCase(
        "project_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}, {"_id": 11, "type": "B"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [{"$project": {"_id": 1, "matchesLet": {"$eq": ["$type", "$$v"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "cat": "A",
                "joined": [{"_id": 10, "matchesLet": True}, {"_id": 11, "matchesLet": False}],
            }
        ],
        msg="$lookup sub-pipeline $project should resolve a let variable",
    ),
    LookupTestCase(
        "group_id_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}, {"_id": 11, "type": "B"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [{"$group": {"_id": "$$v", "count": {"$sum": 1}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "cat": "A", "joined": [{"_id": "A", "count": 2}]}],
        msg="$lookup sub-pipeline $group should resolve a let variable as the group key",
    ),
    LookupTestCase(
        "group_accumulator_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}, {"_id": 11, "type": "B"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [
                        {
                            "$group": {
                                "_id": None,
                                "matching": {"$sum": {"$cond": [{"$eq": ["$type", "$$v"]}, 1, 0]}},
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "cat": "A", "joined": [{"_id": None, "matching": 1}]}],
        msg="$lookup sub-pipeline $group should resolve a let variable inside an "
        "accumulator expression",
    ),
    LookupTestCase(
        "sort_by_count_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}, {"_id": 11, "type": "B"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [{"$sortByCount": "$$v"}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "cat": "A", "joined": [{"_id": "A", "count": 2}]}],
        msg="$lookup sub-pipeline $sortByCount should resolve a let variable",
    ),
    LookupTestCase(
        "bucket_resolves_let",
        foreign_docs=[{"_id": 10, "n": 1}, {"_id": 11, "n": 5}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [
                        {
                            "$bucket": {
                                "groupBy": "$n",
                                "boundaries": [0, 4, 10],
                                "output": {"lv": {"$first": "$$v"}},
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "cat": "A", "joined": [{"_id": 0, "lv": "A"}, {"_id": 4, "lv": "A"}]}],
        msg="$lookup sub-pipeline $bucket should resolve a let variable in output",
    ),
    LookupTestCase(
        "bucket_auto_resolves_let",
        foreign_docs=[{"_id": 10, "n": 1}, {"_id": 11, "n": 5}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [
                        {
                            "$bucketAuto": {
                                "groupBy": "$n",
                                "buckets": 1,
                                "output": {"lv": {"$first": "$$v"}},
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "cat": "A", "joined": [{"_id": {"min": 1, "max": 5}, "lv": "A"}]}],
        msg="$lookup sub-pipeline $bucketAuto should resolve a let variable in output",
    ),
    LookupTestCase(
        "facet_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}, {"_id": 11, "type": "B"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [
                        {"$facet": {"branch": [{"$match": {"$expr": {"$eq": ["$type", "$$v"]}}}]}}
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "cat": "A", "joined": [{"branch": [{"_id": 10, "type": "A"}]}]}],
        msg="$lookup sub-pipeline $facet should resolve a let variable inside a branch pipeline",
    ),
    LookupTestCase(
        "union_with_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [
                        {
                            "$unionWith": {
                                "pipeline": [
                                    {"$documents": [{"src": "union"}]},
                                    {"$addFields": {"lv": "$$v"}},
                                ]
                            }
                        },
                        {"$project": {"_id": 0, "type": 1, "src": 1, "lv": 1}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "cat": "A",
                "joined": [{"type": "A"}, {"src": "union", "lv": "A"}],
            }
        ],
        msg="$lookup sub-pipeline $unionWith should resolve an outer let variable in "
        "its pipeline",
    ),
    LookupTestCase(
        "set_window_fields_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}, {"_id": 11, "type": "B"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [
                        {
                            "$setWindowFields": {
                                "partitionBy": "$$v",
                                "sortBy": {"_id": 1},
                                "output": {"r": {"$rank": {}}},
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "cat": "A",
                "joined": [
                    {"_id": 10, "type": "A", "r": 1},
                    {"_id": 11, "type": "B", "r": 2},
                ],
            }
        ],
        msg="$lookup sub-pipeline $setWindowFields should resolve a let variable "
        "as the partition key",
    ),
    LookupTestCase(
        "fill_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}, {"_id": 11, "type": "B"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [
                        {"$fill": {"sortBy": {"_id": 1}, "output": {"lv": {"value": "$$v"}}}},
                        {"$sort": {"_id": 1}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "cat": "A",
                "joined": [
                    {"_id": 10, "type": "A", "lv": "A"},
                    {"_id": 11, "type": "B", "lv": "A"},
                ],
            }
        ],
        msg="$lookup sub-pipeline $fill should resolve a let variable in an output "
        "value expression",
    ),
    LookupTestCase(
        "redact_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}, {"_id": 11, "type": "B"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [
                        {"$redact": {"$cond": [{"$eq": ["$type", "$$v"]}, "$$KEEP", "$$PRUNE"]}}
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "cat": "A", "joined": [{"_id": 10, "type": "A"}]}],
        msg="$lookup sub-pipeline $redact should resolve a let variable in its expression",
    ),
    LookupTestCase(
        "replace_root_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [{"$replaceRoot": {"newRoot": {"t": "$type", "lv": "$$v"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "cat": "A", "joined": [{"t": "A", "lv": "A"}]}],
        msg="$lookup sub-pipeline $replaceRoot should resolve a let variable in the new root",
    ),
    LookupTestCase(
        "replace_with_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [{"$replaceWith": {"t": "$type", "lv": "$$v"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "cat": "A", "joined": [{"t": "A", "lv": "A"}]}],
        msg="$lookup sub-pipeline $replaceWith should resolve a let variable in the new root",
    ),
    LookupTestCase(
        "graph_lookup_start_with_resolves_let",
        foreign_docs=[{"_id": 10, "type": "A"}, {"_id": 11, "type": "B"}],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [
                        {
                            "$graphLookup": {
                                "from": FOREIGN,
                                "startWith": "$$v",
                                "connectFromField": "type",
                                "connectToField": "type",
                                "as": "g",
                            }
                        },
                        {"$project": {"_id": 1, "gTypes": "$g.type"}},
                        {"$sort": {"_id": 1}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "cat": "A",
                "joined": [
                    {"_id": 10, "gTypes": ["A"]},
                    {"_id": 11, "gTypes": ["A"]},
                ],
            }
        ],
        msg="$lookup sub-pipeline $graphLookup should resolve a let variable in startWith",
    ),
    LookupTestCase(
        "graph_lookup_restrict_search_resolves_let",
        foreign_docs=[
            {"_id": 10, "link": "root", "next": "a", "type": "A"},
            {"_id": 11, "link": "a", "next": "b", "type": "A"},
            {"_id": 12, "link": "b", "next": "c", "type": "B"},
            {"_id": 13, "link": "c", "type": "A"},
        ],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [
                        {"$match": {"_id": 10}},
                        {
                            "$graphLookup": {
                                "from": FOREIGN,
                                "startWith": "$next",
                                "connectFromField": "next",
                                "connectToField": "link",
                                "as": "g",
                                "restrictSearchWithMatch": {"$expr": {"$eq": ["$type", "$$v"]}},
                            }
                        },
                        {"$project": {"_id": 1, "gIds": "$g._id"}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "cat": "A", "joined": [{"_id": 10, "gIds": [11]}]}],
        msg="$lookup sub-pipeline $graphLookup should resolve a let variable in "
        "restrictSearchWithMatch",
    ),
    LookupTestCase(
        "geo_near_resolves_let",
        foreign_indexes=[IndexModel([("loc", "2dsphere")])],
        foreign_docs=[
            {"_id": 10, "type": "A", "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 11, "type": "B", "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        docs=[{"_id": 1, "cat": "A"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"v": "$cat"},
                    "pipeline": [
                        {
                            "$geoNear": {
                                "near": {"type": "Point", "coordinates": [0, 0]},
                                "distanceField": "d",
                                "query": {"$expr": {"$eq": ["$type", "$$v"]}},
                            }
                        },
                        {"$project": {"_id": 1, "type": 1}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "cat": "A", "joined": [{"_id": 10, "type": "A"}]}],
        msg="$lookup sub-pipeline $geoNear should resolve a let variable in its query filter",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_VERBOSE_LET_WIRING_TESTS))
def test_verbose_let_wiring(collection, test_case: LookupTestCase):
    """Test $lookup sub-pipeline stages resolve let variables."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
