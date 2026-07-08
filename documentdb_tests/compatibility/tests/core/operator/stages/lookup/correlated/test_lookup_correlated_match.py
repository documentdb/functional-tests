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

# --- Section 1: Comparison Operators with Let Variables in $expr ---

LOOKUP_MATCH_COMPARISON_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "match_expr_eq",
        docs=[{"_id": 1, "cat": "electronics"}],
        foreign_docs=[
            {"_id": 10, "category": "electronics"},
            {"_id": 11, "category": "clothing"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"localCat": "$cat"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$category", "$$localCat"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "cat": "electronics",
                "joined": [{"_id": 10, "category": "electronics"}],
            }
        ],
        msg="$lookup $match $expr $eq should match foreign docs where field equals let var",
    ),
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
        "match_expr_gt",
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
                    "pipeline": [{"$match": {"$expr": {"$gt": ["$score", "$$min"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "minScore": 70,
                "joined": [{"_id": 10, "score": 80}],
            }
        ],
        msg="$lookup $match $expr $gt should match foreign docs where field > let var",
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

# --- Section 2: Logical Operators Combining Let Variables ---

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

# --- Section 3: Arithmetic in $expr with Let Variables ---

LOOKUP_MATCH_ARITHMETIC_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "match_expr_multiply_let_var",
        docs=[{"_id": 1, "limit": 25}],
        foreign_docs=[
            {"_id": 10, "amount": 60},
            {"_id": 11, "amount": 40},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"lim": "$limit"},
                    "pipeline": [
                        {"$match": {"$expr": {"$gt": ["$amount", {"$multiply": ["$$lim", 2]}]}}}
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "limit": 25,
                "joined": [{"_id": 10, "amount": 60}],
            }
        ],
        msg="$lookup $match $expr with $multiply on let var should compute threshold correctly",
    ),
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

# --- Section 4: Array Operations in $expr with Let Variables ---

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

# --- Section 5: Null/Missing Handling in $match $expr ---

LOOKUP_MATCH_NULL_MISSING_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "match_expr_eq_let_var_null_matches_null",
        docs=[{"_id": 1, "val": None}],
        foreign_docs=[
            {"_id": 10, "field": None},
            {"_id": 11, "field": "something"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$val"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$field", "$$x"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "val": None,
                "joined": [{"_id": 10, "field": None}],
            }
        ],
        msg="$lookup $match $expr $eq with null let var should match foreign null fields",
    ),
    LookupTestCase(
        "match_expr_eq_let_var_missing_vs_null",
        docs=[{"_id": 1}],
        foreign_docs=[
            {"_id": 10, "field": None},
            {"_id": 11, "field": "value"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$nonexistent"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$field", "$$x"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [],
            }
        ],
        msg=(
            "$lookup $match $expr $eq with missing let var should NOT"
            " match foreign null fields (missing != null in $expr $eq)"
        ),
    ),
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

# --- Section 6: $match Without $expr (literal string behavior) ---

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

# --- Section 7: Multiple $match Stages Using Let Variables ---

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

# --- Section 8: Date Comparisons in $expr with Let Variables ---

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

# --- Section 9: Pipeline Cannot Access Outer Fields Directly ---

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
