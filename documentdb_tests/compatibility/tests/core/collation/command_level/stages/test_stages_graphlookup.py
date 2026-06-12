"""Tests for collation effects on $graphLookup equality matching."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [GraphLookup Collation-Sensitive Traversal]: $graphLookup uses
# command-level collation for connectFromField/connectToField equality
# comparisons during recursive traversal, enabling case-insensitive and
# accent-insensitive graph walks.
COLLATION_GRAPHLOOKUP_TRAVERSAL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "graphlookup_case_insensitive_traversal",
        docs=[
            {"_id": 1, "name": "start", "connects": "A"},
            {"_id": 2, "name": "A", "connects": "b"},
            {"_id": 3, "name": "B", "connects": "c"},
            {"_id": 4, "name": "c", "connects": None},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"_id": 1}},
                {
                    "$graphLookup": {
                        "from": ctx.collection,
                        "startWith": "$connects",
                        "connectFromField": "connects",
                        "connectToField": "name",
                        "as": "chain",
                    }
                },
                {"$project": {"_id": 1, "chain._id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "chain": [{"_id": 2}, {"_id": 3}, {"_id": 4}]}],
        ignore_order_in=["chain"],
        msg="$graphLookup with strength 2 should traverse case-insensitively",
    ),
    CommandTestCase(
        "graphlookup_no_collation_binary",
        docs=[
            {"_id": 1, "name": "start", "connects": "A"},
            {"_id": 2, "name": "A", "connects": "b"},
            {"_id": 3, "name": "B", "connects": "c"},
            {"_id": 4, "name": "c", "connects": None},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"_id": 1}},
                {
                    "$graphLookup": {
                        "from": ctx.collection,
                        "startWith": "$connects",
                        "connectFromField": "connects",
                        "connectToField": "name",
                        "as": "chain",
                    }
                },
                {"$project": {"_id": 1, "chain._id": 1}},
            ],
            "cursor": {},
        },
        expected=[{"_id": 1, "chain": [{"_id": 2}]}],
        ignore_order_in=["chain"],
        msg="$graphLookup without collation should stop at case mismatch",
    ),
    CommandTestCase(
        "graphlookup_accent_insensitive_traversal",
        docs=[
            {"_id": 1, "name": "start", "connects": "cafe"},
            {"_id": 2, "name": "caf\u00e9", "connects": "latte"},
            {"_id": 3, "name": "latte", "connects": None},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"_id": 1}},
                {
                    "$graphLookup": {
                        "from": ctx.collection,
                        "startWith": "$connects",
                        "connectFromField": "connects",
                        "connectToField": "name",
                        "as": "chain",
                    }
                },
                {"$project": {"_id": 1, "chain._id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "chain": [{"_id": 2}, {"_id": 3}]}],
        ignore_order_in=["chain"],
        msg="$graphLookup with strength 1 should traverse accent-insensitively",
    ),
    CommandTestCase(
        "graphlookup_max_depth_with_collation",
        docs=[
            {"_id": 1, "name": "start", "connects": "A"},
            {"_id": 2, "name": "a", "connects": "B"},
            {"_id": 3, "name": "b", "connects": "C"},
            {"_id": 4, "name": "c", "connects": None},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"_id": 1}},
                {
                    "$graphLookup": {
                        "from": ctx.collection,
                        "startWith": "$connects",
                        "connectFromField": "connects",
                        "connectToField": "name",
                        "as": "chain",
                        "maxDepth": 1,
                    }
                },
                {"$project": {"_id": 1, "chain._id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "chain": [{"_id": 2}, {"_id": 3}]}],
        ignore_order_in=["chain"],
        msg="$graphLookup with collation and maxDepth should respect both",
    ),
    CommandTestCase(
        "graphlookup_restrictsearchwithmatch_case_insensitive",
        docs=[
            {"_id": 1, "name": "start", "connects": "nodeA", "status": "x"},
            {"_id": 2, "name": "nodeA", "connects": "nodeB", "status": "Active"},
            {"_id": 3, "name": "nodeB", "connects": None, "status": "ACTIVE"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"_id": 1}},
                {
                    "$graphLookup": {
                        "from": ctx.collection,
                        "startWith": "$connects",
                        "connectFromField": "connects",
                        "connectToField": "name",
                        "as": "chain",
                        "restrictSearchWithMatch": {"status": "active"},
                    }
                },
                {"$project": {"_id": 1, "chain._id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "chain": [{"_id": 2}, {"_id": 3}]}],
        ignore_order_in=["chain"],
        msg="$graphLookup restrictSearchWithMatch should use collation for filter matching",
    ),
    CommandTestCase(
        "graphlookup_restrictsearchwithmatch_no_collation",
        docs=[
            {"_id": 1, "name": "start", "connects": "nodeA", "status": "x"},
            {"_id": 2, "name": "nodeA", "connects": "nodeB", "status": "Active"},
            {"_id": 3, "name": "nodeB", "connects": None, "status": "ACTIVE"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"_id": 1}},
                {
                    "$graphLookup": {
                        "from": ctx.collection,
                        "startWith": "$connects",
                        "connectFromField": "connects",
                        "connectToField": "name",
                        "as": "chain",
                        "restrictSearchWithMatch": {"status": "active"},
                    }
                },
                {"$project": {"_id": 1, "chain._id": 1}},
            ],
            "cursor": {},
        },
        expected=[{"_id": 1, "chain": []}],
        msg="$graphLookup restrictSearchWithMatch without collation should use binary matching",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_GRAPHLOOKUP_TRAVERSAL_TESTS))
def test_collation_aggregate_graphlookup(database_client, collection, test):
    """Test collation affects $graphLookup equality matching during traversal."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        ignore_order_in=test.ignore_order_in,
        msg=test.msg,
    )
