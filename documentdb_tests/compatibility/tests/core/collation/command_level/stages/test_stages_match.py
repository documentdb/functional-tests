"""Tests for collation effects on match stage operators."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Match Stage Operators]: collation affects equality ($eq, $ne),
# comparison ($gt, $gte, $lt, $lte), set ($in, $nin, $all), $elemMatch, $expr,
# $not, $nor, $or, and $and within $match; $regex and $exists/$type are NOT
# affected; field path matching always uses binary comparison.
COLLATION_MATCH_OPERATORS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "match_eq_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
            {"_id": 4, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        msg="$match $eq should use collation for case-insensitive matching",
    ),
    CommandTestCase(
        "match_ne_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$ne": "apple"}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 3, "x": "banana"}],
        msg="$match $ne should use collation for case-insensitive exclusion",
    ),
    CommandTestCase(
        "match_gt_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "Banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"x": {"$gt": "apple"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 3, "x": "banana"}, {"_id": 4, "x": "Banana"}],
        msg="$match $gt should use collation for case-insensitive comparison",
    ),
    CommandTestCase(
        "match_gte_lte_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"x": {"$gte": "apple", "$lte": "apple"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="$match $gte/$lte should use collation for case-insensitive range",
    ),
    CommandTestCase(
        "match_lt_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "Banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"x": {"$lt": "banana"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="$match $lt should use collation for case-insensitive comparison",
    ),
    CommandTestCase(
        "match_in_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$in": ["apple"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="$match $in should use collation for case-insensitive set membership",
    ),
    CommandTestCase(
        "match_nin_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$nin": ["apple"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 3, "x": "banana"}],
        msg="$match $nin should use collation for case-insensitive set exclusion",
    ),
    CommandTestCase(
        "match_all_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$all": ["apple"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="$match $all should use collation for case-insensitive matching",
    ),
    CommandTestCase(
        "match_elemmatch_case_insensitive",
        docs=[
            {"_id": 1, "x": ["apple", "banana"]},
            {"_id": 2, "x": ["Apple", "Banana"]},
            {"_id": 3, "x": ["cherry"]},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"x": {"$elemMatch": {"$eq": "apple"}}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": ["apple", "banana"]},
            {"_id": 2, "x": ["Apple", "Banana"]},
        ],
        msg="$match $elemMatch should use collation for case-insensitive matching",
    ),
    CommandTestCase(
        "match_expr_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"$expr": {"$eq": ["$x", "apple"]}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="$match $expr should use collation for case-insensitive comparison",
    ),
    CommandTestCase(
        "match_not_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"x": {"$not": {"$eq": "apple"}}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 3, "x": "banana"}],
        msg="$match $not should use collation for case-insensitive negation",
    ),
    CommandTestCase(
        "match_or_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "cherry"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"$or": [{"x": "apple"}, {"x": "banana"}]}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        msg="$match $or should use collation for case-insensitive matching",
    ),
    CommandTestCase(
        "match_and_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"$and": [{"x": {"$gte": "apple"}}, {"x": {"$lte": "apple"}}]}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="$match $and should use collation for case-insensitive matching",
    ),
    CommandTestCase(
        "match_nor_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"$nor": [{"x": "apple"}]}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 3, "x": "banana"}],
        msg="$match $nor should use collation for case-insensitive exclusion",
    ),
    CommandTestCase(
        "match_regex_not_affected",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$regex": "^apple$"}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="$match $regex should NOT be affected by collation",
    ),
    CommandTestCase(
        "match_exists_not_affected",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"x": {"$exists": True}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="$match $exists should NOT be affected by collation",
    ),
    CommandTestCase(
        "match_type_not_affected",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": 42},
            {"_id": 3, "x": "Apple"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"x": {"$type": "string"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 3, "x": "Apple"}],
        msg="$match $type should NOT be affected by collation",
    ),
    CommandTestCase(
        "match_field_path_binary_comparison",
        docs=[
            {"_id": 1, "Name": "apple"},
            {"_id": 2, "name": "Apple"},
            {"_id": 3, "NAME": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": {"$exists": True}}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 2, "name": "Apple"}],
        msg="field path matching should always use binary comparison regardless of collation",
    ),
    CommandTestCase(
        "match_implicit_array_element_case_insensitive",
        docs=[
            {"_id": 1, "arr": ["Apple", "banana"]},
            {"_id": 2, "arr": ["cherry", "date"]},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"arr": "apple"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "arr": ["Apple", "banana"]}],
        msg="$match implicit array element matching should use collation",
    ),
    CommandTestCase(
        "match_implicit_array_element_no_collation",
        docs=[
            {"_id": 1, "arr": ["Apple", "banana"]},
            {"_id": 2, "arr": ["cherry", "date"]},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"arr": "apple"}}],
            "cursor": {},
        },
        expected=[],
        msg="$match implicit array element matching without collation should use binary comparison",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_MATCH_OPERATORS_TESTS))
def test_collation_aggregate_match(database_client, collection, test):
    """Test collation effects on $match stage operators."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
