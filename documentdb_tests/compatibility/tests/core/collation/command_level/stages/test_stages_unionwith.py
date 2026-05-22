"""Tests for collation propagation into $unionWith sub-pipelines."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import SiblingCollection

# Property [UnionWith Collation Propagation]: command-level collation propagates
# into $unionWith sub-pipelines, affecting $match and $sort within them.
COLLATION_UNIONWITH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unionwith_match_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"x": "apple"}},
                {
                    "$unionWith": {
                        "coll": ctx.collection,
                        "pipeline": [{"$match": {"x": "BANANA"}}],
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "banana"},
        ],
        msg="$unionWith sub-pipeline $match should use command-level collation",
    ),
    CommandTestCase(
        "unionwith_no_collation_binary",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"x": "apple"}},
                {
                    "$unionWith": {
                        "coll": ctx.collection,
                        "pipeline": [{"$match": {"x": "BANANA"}}],
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="$unionWith without collation should use binary comparison",
    ),
    CommandTestCase(
        "unionwith_sort_case_insensitive",
        docs=[
            {"_id": 1, "x": "banana"},
            {"_id": 2, "x": "Apple"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$unionWith": {
                        "coll": ctx.collection,
                        "pipeline": [{"$match": {"_id": 2}}],
                    }
                },
                {"$sort": {"x": 1}},
                {"$project": {"_id": 1, "x": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 2, "x": "Apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 1, "x": "banana"},
        ],
        msg="$unionWith results should sort under command-level collation",
    ),
]

# Property [UnionWith Overrides Foreign Collection Collation]: command-level
# collation overrides the unioned collection's default collation for sub-pipeline
# operations.
COLLATION_UNIONWITH_OVERRIDE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unionwith_overrides_foreign_default",
        docs=[{"_id": 1, "x": "apple"}],
        siblings=[
            SiblingCollection(
                suffix="_other",
                collation={"locale": "fr", "strength": 3},
                docs=[
                    {"_id": 10, "x": "Apple"},
                    {"_id": 11, "x": "banana"},
                ],
            ),
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$unionWith": {
                        "coll": ctx.collection + "_other",
                        "pipeline": [{"$match": {"x": "apple"}}],
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 10, "x": "Apple"},
        ],
        msg="command collation should override unioned collection's default collation",
    ),
]

COLLATION_UNIONWITH_ALL_TESTS: list[CommandTestCase] = (
    COLLATION_UNIONWITH_TESTS + COLLATION_UNIONWITH_OVERRIDE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_UNIONWITH_ALL_TESTS))
def test_collation_aggregate_unionwith(database_client, collection, test):
    """Test collation propagation into $unionWith sub-pipelines."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
