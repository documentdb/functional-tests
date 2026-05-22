"""Tests for collation propagation through non-collation-sensitive stages.

Confirms that collation set at the command level propagates through stages
that do not themselves perform string comparisons ($unwind, $limit, $skip,
$sample) and remains active for subsequent collation-sensitive stages.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Collation Propagation Through Non-Sensitive Stages]: collation
# propagates through $unwind, $limit, $skip, $sample, $addFields, $set, and
# $project, remaining active for subsequent $match and $sort stages.
COLLATION_PROPAGATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "propagates_through_unwind",
        docs=[
            {"_id": 1, "tags": ["Apple", "banana"]},
            {"_id": 2, "tags": ["cherry"]},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$unwind": "$tags"},
                {"$match": {"tags": "apple"}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "tags": "Apple"}],
        msg="collation should propagate through $unwind to subsequent $match",
    ),
    CommandTestCase(
        "propagates_through_limit",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$limit": 3},
                {"$match": {"x": "apple"}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        msg="collation should propagate through $limit to subsequent $match",
    ),
    CommandTestCase(
        "propagates_through_skip",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$skip": 1},
                {"$match": {"x": "apple"}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 2, "x": "Apple"}],
        msg="collation should propagate through $skip to subsequent $match",
    ),
    CommandTestCase(
        "propagates_through_unwind_to_sort",
        docs=[
            {"_id": 1, "items": ["banana", "Apple", "cherry"]},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$unwind": "$items"},
                {"$sort": {"items": 1}},
                {"$project": {"_id": 0, "items": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"items": "Apple"},
            {"items": "banana"},
            {"items": "cherry"},
        ],
        msg="collation should propagate through $unwind to subsequent $sort",
    ),
    CommandTestCase(
        "propagates_through_multiple_stages",
        docs=[
            {"_id": 1, "tags": ["Apple", "BANANA"], "cat": "fruit"},
            {"_id": 2, "tags": ["cherry"], "cat": "Fruit"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"cat": "fruit"}},
                {"$unwind": "$tags"},
                {"$sort": {"tags": 1}},
                {"$skip": 1},
                {"$limit": 2},
                {"$project": {"_id": 1, "tags": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "tags": "BANANA"},
            {"_id": 2, "tags": "cherry"},
        ],
        msg="collation should propagate through chained non-sensitive stages",
    ),
    CommandTestCase(
        "propagates_through_addfields",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$addFields": {"y": "computed"}},
                {"$match": {"x": "apple"}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple", "y": "computed"},
            {"_id": 2, "x": "Apple", "y": "computed"},
        ],
        msg="collation should propagate through $addFields to subsequent $match",
    ),
    CommandTestCase(
        "propagates_through_set",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$set": {"y": "computed"}},
                {"$match": {"x": "apple"}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple", "y": "computed"},
            {"_id": 2, "x": "Apple", "y": "computed"},
        ],
        msg="collation should propagate through $set to subsequent $match",
    ),
    CommandTestCase(
        "propagates_through_project",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$project": {"x": 1}},
                {"$match": {"x": "apple"}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        msg="collation should propagate through $project to subsequent $match",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_PROPAGATION_TESTS))
def test_collation_aggregate_propagation(database_client, collection, test):
    """Test collation propagates through non-collation-sensitive stages."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
