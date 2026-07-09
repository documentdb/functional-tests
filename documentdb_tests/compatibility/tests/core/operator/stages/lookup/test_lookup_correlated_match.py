"""Tests for $lookup correlated subquery — $match with $expr using let variables.

Covers the primary use case for correlated $lookup: filtering foreign documents
using let variables inside $match with $expr. Includes comparison operators,
logical operators, arithmetic, string/array operations, date comparisons,
null/missing handling, and literal behavior without $expr.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Correlated Subquery — $match/$expr]: let variables are usable inside
# $match with $expr for all comparison, logical, arithmetic, array, and date
# operators; without $expr the variable reference is a literal string.


LOOKUP_MATCH_COMPARISON_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "match_expr_ne",
        docs=[{"_id": 1, "exclude": "inactive"}],
        foreign_docs=[
            {"_id": 10, "status": "active"},
            {"_id": 11, "status": "inactive"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"excl": "$exclude"},
                    "pipeline": [{"$match": {"$expr": {"$ne": ["$status", "$$excl"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "exclude": "inactive",
                "joined": [{"_id": 10, "status": "active"}],
            }
        ],
        msg="$lookup $match $expr $ne should match foreign docs where field differs from let var",
    ),
    LookupTestCase(
        "match_expr_gte",
        docs=[{"_id": 1, "minScore": 70}],
        foreign_docs=[
            {"_id": 10, "score": 80},
            {"_id": 11, "score": 60},
            {"_id": 12, "score": 70},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"min": "$minScore"},
                    "pipeline": [{"$match": {"$expr": {"$gte": ["$score", "$$min"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "minScore": 70,
                "joined": [{"_id": 10, "score": 80}, {"_id": 12, "score": 70}],
            }
        ],
        msg="$lookup $match $expr $gte should match foreign docs where field >= let var",
    ),
    LookupTestCase(
        "match_expr_lt",
        docs=[{"_id": 1, "maxPrice": 50}],
        foreign_docs=[
            {"_id": 10, "price": 30},
            {"_id": 11, "price": 70},
            {"_id": 12, "price": 50},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"maxP": "$maxPrice"},
                    "pipeline": [{"$match": {"$expr": {"$lt": ["$price", "$$maxP"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "maxPrice": 50,
                "joined": [{"_id": 10, "price": 30}],
            }
        ],
        msg="$lookup $match $expr $lt should match foreign docs where field < let var",
    ),
    LookupTestCase(
        "match_expr_lte",
        docs=[{"_id": 1, "maxPrice": 50}],
        foreign_docs=[
            {"_id": 10, "price": 30},
            {"_id": 11, "price": 70},
            {"_id": 12, "price": 50},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"maxP": "$maxPrice"},
                    "pipeline": [{"$match": {"$expr": {"$lte": ["$price", "$$maxP"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "maxPrice": 50,
                "joined": [{"_id": 10, "price": 30}, {"_id": 12, "price": 50}],
            }
        ],
        msg="$lookup $match $expr $lte should match foreign docs where field <= let var",
    ),
]


LOOKUP_MATCH_LOGICAL_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "match_expr_and_two_let_vars",
        docs=[{"_id": 1, "wantType": "A", "minScore": 50}],
        foreign_docs=[
            {"_id": 10, "type": "A", "score": 80},
            {"_id": 11, "type": "A", "score": 30},
            {"_id": 12, "type": "B", "score": 90},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"t": "$wantType", "min": "$minScore"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$type", "$$t"]},
                                        {"$gte": ["$score", "$$min"]},
                                    ]
                                }
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
                "wantType": "A",
                "minScore": 50,
                "joined": [{"_id": 10, "type": "A", "score": 80}],
            }
        ],
        msg="$lookup $match $expr $and should apply both let var conditions",
    ),
    LookupTestCase(
        "match_expr_or_two_let_vars",
        docs=[{"_id": 1, "cat1": "electronics", "cat2": "books"}],
        foreign_docs=[
            {"_id": 10, "category": "electronics"},
            {"_id": 11, "category": "clothing"},
            {"_id": 12, "category": "books"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"c1": "$cat1", "c2": "$cat2"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$or": [
                                        {"$eq": ["$category", "$$c1"]},
                                        {"$eq": ["$category", "$$c2"]},
                                    ]
                                }
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
                "cat1": "electronics",
                "cat2": "books",
                "joined": [
                    {"_id": 10, "category": "electronics"},
                    {"_id": 12, "category": "books"},
                ],
            }
        ],
        msg="$lookup $match $expr $or should match when either let var condition is met",
    ),
    LookupTestCase(
        "match_expr_not_with_let_var",
        docs=[{"_id": 1, "excludeStatus": "deleted"}],
        foreign_docs=[
            {"_id": 10, "status": "active"},
            {"_id": 11, "status": "deleted"},
            {"_id": 12, "status": "pending"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"excl": "$excludeStatus"},
                    "pipeline": [{"$match": {"$expr": {"$not": [{"$eq": ["$status", "$$excl"]}]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "excludeStatus": "deleted",
                "joined": [
                    {"_id": 10, "status": "active"},
                    {"_id": 12, "status": "pending"},
                ],
            }
        ],
        msg="$lookup $match $expr $not should exclude docs matching the let var",
    ),
]


LOOKUP_MATCH_ARITHMETIC_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "match_expr_add_let_var",
        docs=[{"_id": 1, "base": 40}],
        foreign_docs=[
            {"_id": 10, "price": 45},
            {"_id": 11, "price": 55},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"b": "$base"},
                    "pipeline": [{"$match": {"$expr": {"$lt": ["$price", {"$add": ["$$b", 10]}]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "base": 40,
                "joined": [{"_id": 10, "price": 45}],
            }
        ],
        msg="$lookup $match $expr with $add on let var should compute threshold correctly",
    ),
    LookupTestCase(
        "match_expr_subtract_let_var",
        docs=[{"_id": 1, "target": 100}],
        foreign_docs=[
            {"_id": 10, "qty": 90},
            {"_id": 11, "qty": 96},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"tgt": "$target"},
                    "pipeline": [
                        {"$match": {"$expr": {"$gte": ["$qty", {"$subtract": ["$$tgt", 5]}]}}}
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "target": 100,
                "joined": [{"_id": 11, "qty": 96}],
            }
        ],
        msg="$lookup $match $expr with $subtract on let var should compute threshold correctly",
    ),
]


LOOKUP_MATCH_ARRAY_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "match_expr_in_let_var_is_element",
        docs=[{"_id": 1, "wantedTag": "python"}],
        foreign_docs=[
            {"_id": 10, "tags": ["python", "java"]},
            {"_id": 11, "tags": ["rust", "go"]},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"tag": "$wantedTag"},
                    "pipeline": [{"$match": {"$expr": {"$in": ["$$tag", "$tags"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "wantedTag": "python",
                "joined": [{"_id": 10, "tags": ["python", "java"]}],
            }
        ],
        msg="$lookup $match $expr $in with let var as element should find it in foreign array",
    ),
    LookupTestCase(
        "match_expr_in_let_var_is_array",
        docs=[{"_id": 1, "allowed": ["python", "rust"]}],
        foreign_docs=[
            {"_id": 10, "lang": "python"},
            {"_id": 11, "lang": "java"},
            {"_id": 12, "lang": "rust"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"allowedTags": "$allowed"},
                    "pipeline": [{"$match": {"$expr": {"$in": ["$lang", "$$allowedTags"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "allowed": ["python", "rust"],
                "joined": [
                    {"_id": 10, "lang": "python"},
                    {"_id": 12, "lang": "rust"},
                ],
            }
        ],
        msg="$lookup $match $expr $in with let var as array should match foreign elements in it",
    ),
    LookupTestCase(
        "match_expr_setIntersection_overlap",
        docs=[{"_id": 1, "wanted": ["A", "B"]}],
        foreign_docs=[
            {"_id": 10, "cats": ["A", "C"]},
            {"_id": 11, "cats": ["D", "E"]},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"w": "$wanted"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$gt": [
                                        {"$size": {"$setIntersection": ["$cats", "$$w"]}},
                                        0,
                                    ]
                                }
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
                "wanted": ["A", "B"],
                "joined": [{"_id": 10, "cats": ["A", "C"]}],
            }
        ],
        msg="$lookup $match $expr with $setIntersection should find foreign docs with overlap",
    ),
]


LOOKUP_MATCH_NULL_MISSING_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "match_expr_ifNull_wrapping_let_var",
        docs=[{"_id": 1, "maybe": None}],
        foreign_docs=[
            {"_id": 10, "field": "fallback"},
            {"_id": 11, "field": "other"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$maybe"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$field", {"$ifNull": ["$$x", "fallback"]}]}}}
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "maybe": None,
                "joined": [{"_id": 10, "field": "fallback"}],
            }
        ],
        msg="$lookup $match $expr with $ifNull wrapping null let var should use default value",
    ),
]


LOOKUP_MATCH_WITHOUT_EXPR_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "match_without_expr_gt_treats_var_as_string",
        docs=[{"_id": 1, "minAge": 25}],
        foreign_docs=[
            {"_id": 10, "age": 30},
            {"_id": 11, "age": "$$minAge"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"minAge": "$minAge"},
                    "pipeline": [{"$match": {"age": {"$gt": "$$minAge"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "minAge": 25,
                "joined": [],
            }
        ],
        msg=(
            "$lookup $match without $expr should treat $$var as literal"
            " string in $gt operator (no numeric comparison)"
        ),
    ),
    LookupTestCase(
        "match_mixing_plain_and_expr",
        docs=[{"_id": 1, "localType": "premium"}],
        foreign_docs=[
            {"_id": 10, "status": "active", "type": "premium"},
            {"_id": 11, "status": "active", "type": "basic"},
            {"_id": 12, "status": "inactive", "type": "premium"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"t": "$localType"},
                    "pipeline": [
                        {
                            "$match": {
                                "status": "active",
                                "$expr": {"$eq": ["$type", "$$t"]},
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
                "localType": "premium",
                "joined": [{"_id": 10, "status": "active", "type": "premium"}],
            }
        ],
        msg=(
            "$lookup $match mixing plain query with $expr should apply"
            " both conditions — plain filter and let-variable comparison"
        ),
    ),
    LookupTestCase(
        "match_plain_query_no_let_interaction",
        docs=[{"_id": 1, "status": "archived"}],
        foreign_docs=[
            {"_id": 10, "status": "active"},
            {"_id": 11, "status": "archived"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"s": "$status"},
                    "pipeline": [{"$match": {"status": "active"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "status": "archived",
                "joined": [{"_id": 10, "status": "active"}],
            }
        ],
        msg=(
            "$lookup $match with plain query should filter foreign docs"
            " independently of let vars (matches foreign status, not outer)"
        ),
    ),
]


LOOKUP_MATCH_MULTIPLE_STAGES_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "match_two_stages_cumulative_filter",
        docs=[{"_id": 1, "minScore": 50, "maxPrice": 100}],
        foreign_docs=[
            {"_id": 10, "score": 80, "price": 90},
            {"_id": 11, "score": 80, "price": 150},
            {"_id": 12, "score": 30, "price": 50},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"min": "$minScore", "maxP": "$maxPrice"},
                    "pipeline": [
                        {"$match": {"$expr": {"$gte": ["$score", "$$min"]}}},
                        {"$match": {"$expr": {"$lte": ["$price", "$$maxP"]}}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "minScore": 50,
                "maxPrice": 100,
                "joined": [{"_id": 10, "score": 80, "price": 90}],
            }
        ],
        msg=(
            "$lookup with two $match $expr stages should apply both"
            " filters cumulatively using different let variables"
        ),
    ),
    LookupTestCase(
        "match_expr_then_plain_match",
        docs=[{"_id": 1, "wantType": "A"}],
        foreign_docs=[
            {"_id": 10, "type": "A", "active": True},
            {"_id": 11, "type": "A", "active": False},
            {"_id": 12, "type": "B", "active": True},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"t": "$wantType"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$type", "$$t"]}}},
                        {"$match": {"active": True}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "wantType": "A",
                "joined": [{"_id": 10, "type": "A", "active": True}],
            }
        ],
        msg=(
            "$lookup with $match $expr followed by plain $match should"
            " apply both correlated and non-correlated filters"
        ),
    ),
]


_DATE_CUTOFF = datetime(2024, 6, 1, tzinfo=timezone.utc)
_DATE_BEFORE = datetime(2024, 5, 15, tzinfo=timezone.utc)
_DATE_AFTER = datetime(2024, 7, 10, tzinfo=timezone.utc)

LOOKUP_MATCH_DATE_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "match_expr_date_gt_let_var",
        docs=[{"_id": 1, "cutoff": _DATE_CUTOFF}],
        foreign_docs=[
            {"_id": 10, "eventDate": _DATE_AFTER},
            {"_id": 11, "eventDate": _DATE_BEFORE},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"cutoffDate": "$cutoff"},
                    "pipeline": [{"$match": {"$expr": {"$gt": ["$eventDate", "$$cutoffDate"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "cutoff": _DATE_CUTOFF,
                "joined": [{"_id": 10, "eventDate": _DATE_AFTER}],
            }
        ],
        msg="$lookup $match $expr $gt with date let var should find events after cutoff",
    ),
    LookupTestCase(
        "match_expr_date_lt_let_var",
        docs=[{"_id": 1, "deadline": _DATE_CUTOFF}],
        foreign_docs=[
            {"_id": 10, "createdAt": _DATE_BEFORE},
            {"_id": 11, "createdAt": _DATE_AFTER},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"dl": "$deadline"},
                    "pipeline": [{"$match": {"$expr": {"$lt": ["$createdAt", "$$dl"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "deadline": _DATE_CUTOFF,
                "joined": [{"_id": 10, "createdAt": _DATE_BEFORE}],
            }
        ],
        msg="$lookup $match $expr $lt with date let var should find docs before deadline",
    ),
]


LOOKUP_MATCH_FIELD_ACCESS_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "match_plain_filter_resolves_against_foreign",
        docs=[{"_id": 1, "status": "outer_active"}],
        foreign_docs=[
            {"_id": 10, "status": "active"},
            {"_id": 11, "status": "inactive"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$status"},
                    "pipeline": [{"$match": {"status": "active"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "status": "outer_active",
                "joined": [{"_id": 10, "status": "active"}],
            }
        ],
        msg=(
            "$lookup sub-pipeline $match without $expr resolves field"
            " values against foreign collection, not outer document"
        ),
    ),
]


LOOKUP_MATCH_ADDITIONAL_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "expr_gt_against_let_var",
        docs=[{"_id": 1, "val": 5}],
        foreign_docs=[
            {"_id": 10, "ff": 4},
            {"_id": 11, "ff": 5},
            {"_id": 12, "ff": 6},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$val"},
                    "pipeline": [{"$match": {"$expr": {"$gt": ["$ff", "$$x"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "val": 5, "joined": [{"_id": 12, "ff": 6}]}],
        msg=(
            "$lookup sub-pipeline $match $expr $gt should return"
            " foreign docs greater than the let var"
        ),
    ),
    LookupTestCase(
        "expr_range_with_two_let_vars_on_both_sides",
        docs=[{"_id": 1, "lo": 2, "hi": 8}],
        foreign_docs=[
            {"_id": 10, "ff": 1},
            {"_id": 11, "ff": 5},
            {"_id": 12, "ff": 9},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"lo": "$lo", "hi": "$hi"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$lt": ["$$lo", "$ff"]},
                                        {"$lt": ["$ff", "$$hi"]},
                                    ]
                                }
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "lo": 2, "hi": 8, "joined": [{"_id": 11, "ff": 5}]}],
        msg="$lookup sub-pipeline $expr with let vars on both sides should filter a strict range",
    ),
    LookupTestCase(
        "expr_not_in_membership_with_let_array",
        docs=[{"_id": 1, "la": [1, 2, 3]}],
        foreign_docs=[
            {"_id": 10, "ff": 2},
            {"_id": 11, "ff": 5},
            {"_id": 12, "ff": 1},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"arr": "$la"},
                    "pipeline": [{"$match": {"$expr": {"$not": [{"$in": ["$ff", "$$arr"]}]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "la": [1, 2, 3], "joined": [{"_id": 11, "ff": 5}]}],
        msg=(
            "$lookup sub-pipeline $expr $not $in should return"
            " the complement of the let array membership"
        ),
    ),
    LookupTestCase(
        "expr_size_gate_all_or_nothing_per_input_doc",
        docs=[
            {"_id": 1, "la": [1, 2, 3]},
            {"_id": 2, "la": [1, 2]},
        ],
        foreign_docs=[
            {"_id": 10},
            {"_id": 11},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"arr": "$la"},
                    "pipeline": [{"$match": {"$expr": {"$eq": [{"$size": "$$arr"}, 3]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "la": [1, 2, 3], "joined": [{"_id": 10}, {"_id": 11}]},
            {"_id": 2, "la": [1, 2], "joined": []},
        ],
        msg=(
            "$lookup sub-pipeline $expr $size gate should include"
            " all or no foreign docs per input document"
        ),
    ),
    LookupTestCase(
        "expr_set_is_subset_with_let_array",
        docs=[{"_id": 1, "la": [1, 2]}],
        foreign_docs=[
            {"_id": 10, "farr": [1, 2, 3]},
            {"_id": 11, "farr": [1, 4]},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"arr": "$la"},
                    "pipeline": [{"$match": {"$expr": {"$setIsSubset": ["$$arr", "$farr"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "la": [1, 2], "joined": [{"_id": 10, "farr": [1, 2, 3]}]}],
        msg=(
            "$lookup sub-pipeline $expr $setIsSubset should return foreign docs"
            " whose array is a superset of the let array"
        ),
    ),
    LookupTestCase(
        "expr_cond_selects_field_by_let_flag",
        docs=[
            {"_id": 1, "flag": True, "target": "m"},
            {"_id": 2, "flag": False, "target": "m"},
        ],
        foreign_docs=[
            {"_id": 10, "f1": "m", "f2": "n"},
            {"_id": 11, "f1": "x", "f2": "m"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"flag": "$flag", "target": "$target"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": [
                                        {
                                            "$cond": [
                                                "$$flag",
                                                "$f1",
                                                "$f2",
                                            ]
                                        },
                                        "$$target",
                                    ]
                                }
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
                "flag": True,
                "target": "m",
                "joined": [{"_id": 10, "f1": "m", "f2": "n"}],
            },
            {
                "_id": 2,
                "flag": False,
                "target": "m",
                "joined": [{"_id": 11, "f1": "x", "f2": "m"}],
            },
        ],
        msg=(
            "$lookup sub-pipeline $expr $cond should select the"
            " compared field per input-doc let flag"
        ),
    ),
    LookupTestCase(
        "expr_switch_branches_keyed_on_let_var",
        docs=[
            {"_id": 1, "sel": "hi"},
            {"_id": 2, "sel": "lo"},
            {"_id": 3, "sel": "other"},
        ],
        foreign_docs=[
            {"_id": 10, "fnum": 15},
            {"_id": 11, "fnum": 5},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"sel": "$sel"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$switch": {
                                        "branches": [
                                            {
                                                "case": {"$eq": ["$$sel", "hi"]},
                                                "then": {"$gt": ["$fnum", 10]},
                                            },
                                            {
                                                "case": {"$eq": ["$$sel", "lo"]},
                                                "then": {"$lt": ["$fnum", 10]},
                                            },
                                        ],
                                        "default": False,
                                    }
                                }
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "sel": "hi", "joined": [{"_id": 10, "fnum": 15}]},
            {"_id": 2, "sel": "lo", "joined": [{"_id": 11, "fnum": 5}]},
            {"_id": 3, "sel": "other", "joined": []},
        ],
        msg=(
            "$lookup sub-pipeline $expr $switch should pick the branch matching"
            " the let var and fall through to default"
        ),
    ),
    LookupTestCase(
        "expr_array_elem_at_on_let_array",
        docs=[{"_id": 1, "la": [7, 8]}],
        foreign_docs=[
            {"_id": 10, "ff": 7},
            {"_id": 11, "ff": 8},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"arr": "$la"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": [
                                        {"$arrayElemAt": ["$$arr", 0]},
                                        "$ff",
                                    ]
                                }
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "la": [7, 8], "joined": [{"_id": 10, "ff": 7}]}],
        msg="$lookup sub-pipeline $expr $arrayElemAt should access an element of a let-bound array",
    ),
]


# --- Combine all tests ---
LOOKUP_CORRELATED_MATCH_ALL: list[LookupTestCase] = (
    LOOKUP_MATCH_COMPARISON_TESTS
    + LOOKUP_MATCH_LOGICAL_TESTS
    + LOOKUP_MATCH_ARITHMETIC_TESTS
    + LOOKUP_MATCH_ARRAY_TESTS
    + LOOKUP_MATCH_NULL_MISSING_TESTS
    + LOOKUP_MATCH_WITHOUT_EXPR_TESTS
    + LOOKUP_MATCH_MULTIPLE_STAGES_TESTS
    + LOOKUP_MATCH_DATE_TESTS
    + LOOKUP_MATCH_FIELD_ACCESS_TESTS
    + LOOKUP_MATCH_ADDITIONAL_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_CORRELATED_MATCH_ALL))
def test_lookup_correlated_match(collection, test_case: LookupTestCase):
    """Test $lookup correlated subquery $match with $expr using let variables."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
