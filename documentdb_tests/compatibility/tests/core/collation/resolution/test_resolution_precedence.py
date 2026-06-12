"""Tests for collation inheritance, multi-stage application, and parameter interactions."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

# Property [Collation Inheritance from Collection Default]: when collation is
# omitted, null, or empty from the aggregate command, the collection's default
# collation is used; an explicit collation overrides the collection default.
COLLATION_INHERITANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "inherit_omitted_uses_collection_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}, {"_id": 3, "x": "APPLE"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        msg="aggregate should use collection default collation when collation is omitted",
    ),
    CommandTestCase(
        "inherit_null_uses_collection_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}, {"_id": 3, "x": "APPLE"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
            "collation": None,
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        msg="aggregate should use collection default collation when collation is null",
    ),
    CommandTestCase(
        "inherit_empty_uses_collection_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}, {"_id": 3, "x": "APPLE"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
            "collation": {},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        msg="aggregate should use collection default collation when collation is empty",
    ),
    CommandTestCase(
        "inherit_explicit_overrides_collection_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}, {"_id": 3, "x": "APPLE"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="aggregate should override collection default when explicit collation is provided",
    ),
    CommandTestCase(
        "inherit_simple_overrides_collection_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}, {"_id": 3, "x": "APPLE"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
            "collation": {"locale": "simple"},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="aggregate should override collection default with locale simple for binary comparison",
    ),
]

# Property [Multi-Stage Uniform Application]: all collation-sensitive stages in
# a single pipeline use the command-level collation uniformly.
COLLATION_MULTI_STAGE_UNIFORM_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "multi_stage_two_match_stages",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "Banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"x": "apple"}},
                {"$match": {"x": "APPLE"}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        msg="two $match stages in one pipeline should both use command-level collation",
    ),
    CommandTestCase(
        "multi_stage_match_group_sort",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 2},
            {"_id": 3, "x": "banana", "v": 3},
            {"_id": 4, "x": "Banana", "v": 4},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"x": {"$in": ["apple", "banana"]}}},
                {"$group": {"_id": "$x", "total": {"$sum": "$v"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": "apple", "total": 3},
            {"_id": "banana", "total": 7},
        ],
        msg="$match + $group + $sort pipeline should apply the same collation to all stages",
    ),
]

# Property [Parameter Interaction Edge Cases]: multiple collation parameters
# combine independently, each applying its own effect without conflict.
COLLATION_PARAMETER_INTERACTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "interaction_caselevel_strength1_casefirst_upper",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "\u00e1"},
            {"_id": 4, "x": "b"},
            {"_id": 5, "x": "B"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 1,
                "caseLevel": True,
                "caseFirst": "upper",
            },
        },
        expected=[
            {"_id": 2, "x": "A"},
            {"_id": 1, "x": "a"},
            {"_id": 3, "x": "\u00e1"},
            {"_id": 5, "x": "B"},
            {"_id": 4, "x": "b"},
        ],
        msg="caseLevel+strength1+caseFirst upper should sort uppercase first and ignore accents",
    ),
    CommandTestCase(
        "interaction_shifted_numeric_ordering",
        docs=[
            {"_id": 1, "x": "file 2"},
            {"_id": 2, "x": "file 10"},
            {"_id": 3, "x": "file2"},
            {"_id": 4, "x": "file10"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "numericOrdering": True,
                "alternate": "shifted",
            },
        },
        expected=[
            {"_id": 1, "x": "file 2"},
            {"_id": 3, "x": "file2"},
            {"_id": 2, "x": "file 10"},
            {"_id": 4, "x": "file10"},
        ],
        msg="shifted+numericOrdering should make space ignorable while preserving numeric sort",
    ),
    CommandTestCase(
        "interaction_shifted_punct_strength1_match",
        docs=[
            {"_id": 1, "x": "a_b"},
            {"_id": 2, "x": "a-b"},
            {"_id": 3, "x": "a b"},
            {"_id": 4, "x": "ab"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 1,
                "alternate": "shifted",
                "maxVariable": "punct",
            },
        },
        expected=[
            {"_id": 1, "x": "a_b"},
            {"_id": 2, "x": "a-b"},
            {"_id": 3, "x": "a b"},
            {"_id": 4, "x": "ab"},
        ],
        msg="shifted+punct+strength1 should treat all punctuation and whitespace as ignorable",
    ),
    CommandTestCase(
        "interaction_caselevel_shifted_strength1_match",
        docs=[
            {"_id": 1, "x": "a-b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "Ab"},
            {"_id": 4, "x": "AB"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 1,
                "caseLevel": True,
                "alternate": "shifted",
            },
        },
        expected=[
            {"_id": 1, "x": "a-b"},
            {"_id": 2, "x": "ab"},
        ],
        msg="caseLevel+shifted+strength1 should ignore punctuation but distinguish case",
    ),
    CommandTestCase(
        "interaction_backwards_casefirst_upper",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "b"},
            {"_id": 4, "x": "B"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 3,
                "backwards": True,
                "caseFirst": "upper",
            },
        },
        expected=[
            {"_id": 2, "x": "A"},
            {"_id": 1, "x": "a"},
            {"_id": 4, "x": "B"},
            {"_id": 3, "x": "b"},
        ],
        msg="backwards+caseFirst upper should work independently without conflict",
    ),
    CommandTestCase(
        "interaction_backwards_numeric_ordering",
        docs=[
            {"_id": 1, "x": "a2"},
            {"_id": 2, "x": "a10"},
            {"_id": 3, "x": "a1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 3,
                "backwards": True,
                "numericOrdering": True,
            },
        },
        expected=[
            {"_id": 3, "x": "a1"},
            {"_id": 1, "x": "a2"},
            {"_id": 2, "x": "a10"},
        ],
        msg="backwards+numericOrdering should work independently without conflict",
    ),
    CommandTestCase(
        "interaction_backwards_shifted",
        docs=[
            {"_id": 1, "x": "a-b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a b"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 3,
                "backwards": True,
                "alternate": "shifted",
            },
        },
        expected=[
            {"_id": 1, "x": "a-b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a b"},
        ],
        msg="backwards+shifted should work independently without conflict",
    ),
    CommandTestCase(
        "interaction_backwards_caselevel_strength2",
        docs=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "strength": 2,
                "backwards": True,
                "caseLevel": True,
            },
        },
        expected=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        msg="backwards+caseLevel+strength2 should reverse diacritic comparison direction",
    ),
]

COLLATION_AGGREGATE_RESOLUTION_TESTS: list[CommandTestCase] = (
    COLLATION_INHERITANCE_TESTS
    + COLLATION_MULTI_STAGE_UNIFORM_TESTS
    + COLLATION_PARAMETER_INTERACTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_AGGREGATE_RESOLUTION_TESTS))
def test_collation_aggregate_resolution(database_client, collection, test):
    """Test collation inheritance and resolution precedence in aggregate."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
