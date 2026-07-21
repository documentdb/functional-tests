"""Tests for collation precedence and cross-collection resolution in $lookup joins."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CustomCollection,
    SiblingCollection,
)

# Property [Lookup Collation Precedence]: an equality $lookup join inherits the
# source collection's default collation when the command omits collation, and a
# command-level collation overrides both the source and foreign collection
# defaults.
COLLATION_LOOKUP_PRECEDENCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "lookup_inherits_source_collection_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        siblings=[
            SiblingCollection(
                suffix="_foreign",
                docs=[{"_id": 10, "x": "Apple"}, {"_id": 11, "x": "banana"}],
            ),
        ],
        docs=[{"_id": 1, "x": "apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection + "_foreign",
                        "localField": "x",
                        "foreignField": "x",
                        "as": "matched",
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": "apple", "matched": [{"_id": 10, "x": "Apple"}]}],
        msg="$lookup join should inherit the source collection default collation "
        "when command collation is omitted",
    ),
    CommandTestCase(
        "lookup_command_collation_overrides_source_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        siblings=[
            SiblingCollection(
                suffix="_foreign",
                docs=[{"_id": 10, "x": "Apple"}, {"_id": 11, "x": "banana"}],
            ),
        ],
        docs=[{"_id": 1, "x": "apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection + "_foreign",
                        "localField": "x",
                        "foreignField": "x",
                        "as": "matched",
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "simple"},
        },
        expected=[{"_id": 1, "x": "apple", "matched": []}],
        msg="$lookup join should use command-level collation over the source collection default",
    ),
    CommandTestCase(
        "lookup_command_collation_overrides_foreign_default",
        siblings=[
            SiblingCollection(
                suffix="_foreign",
                collation={"locale": "fr", "strength": 3},
                docs=[{"_id": 10, "x": "Apple"}, {"_id": 11, "x": "banana"}],
            ),
        ],
        docs=[{"_id": 1, "x": "apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection + "_foreign",
                        "localField": "x",
                        "foreignField": "x",
                        "as": "matched",
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "x": "apple", "matched": [{"_id": 10, "x": "Apple"}]}],
        msg="$lookup join should use command-level collation over the foreign "
        "collection default",
    ),
]

# Property [Lookup Cross-Collection Resolution]: the source collection's
# collation governs the join and the foreign collection's default is ignored,
# whether the source has its own default or falls back to binary.
COLLATION_LOOKUP_CROSS_COLLECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "lookup_source_default_governs_over_foreign_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        siblings=[
            SiblingCollection(
                suffix="_foreign",
                collation={"locale": "fr", "strength": 3},
                docs=[{"_id": 10, "x": "Apple"}, {"_id": 11, "x": "banana"}],
            ),
        ],
        docs=[{"_id": 1, "x": "apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection + "_foreign",
                        "localField": "x",
                        "foreignField": "x",
                        "as": "matched",
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": "apple", "matched": [{"_id": 10, "x": "Apple"}]}],
        msg="$lookup join should use the source collection default collation over "
        "a differing foreign collection default",
    ),
    CommandTestCase(
        "lookup_foreign_default_ignored_without_source_default",
        siblings=[
            SiblingCollection(
                suffix="_foreign",
                collation={"locale": "fr", "strength": 3},
                docs=[{"_id": 10, "x": "Apple"}, {"_id": 11, "x": "banana"}],
            ),
        ],
        docs=[{"_id": 1, "x": "apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection + "_foreign",
                        "localField": "x",
                        "foreignField": "x",
                        "as": "matched",
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": "apple", "matched": []}],
        msg="$lookup join should ignore the foreign collection default and fall "
        "back to binary when neither the source nor the command specifies collation",
    ),
]

# Property [Lookup Index Collation Not A Matching Source]: a collated index on
# the foreign field does not change the join result, which follows command and
# collection collation rather than the index collation.
COLLATION_LOOKUP_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "lookup_index_collation_not_used_for_matching",
        siblings=[
            SiblingCollection(
                suffix="_foreign",
                indexes=[IndexModel([("name", 1)], collation={"locale": "en", "strength": 1})],
                docs=[{"_id": 10, "name": "apple"}],
            ),
        ],
        docs=[{"_id": 1, "product": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection + "_foreign",
                        "localField": "product",
                        "foreignField": "name",
                        "as": "matched",
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        expected=[{"_id": 1, "product": "Apple", "matched": []}],
        msg="$lookup should not use a case-insensitive foreign index collation "
        "for matching when no command or collection collation applies",
    ),
    CommandTestCase(
        "lookup_index_collation_does_not_interfere",
        siblings=[
            SiblingCollection(
                suffix="_foreign",
                indexes=[IndexModel([("name", 1)], collation={"locale": "en", "strength": 1})],
                docs=[{"_id": 10, "name": "apple"}],
            ),
        ],
        docs=[{"_id": 1, "product": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection + "_foreign",
                        "localField": "product",
                        "foreignField": "name",
                        "as": "matched",
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "product": "Apple", "matched": [{"_id": 10, "name": "apple"}]}],
        msg="$lookup should follow command collation and not be disrupted by a "
        "foreign index collation",
    ),
]

COLLATION_LOOKUP_RESOLUTION_TESTS: list[CommandTestCase] = (
    COLLATION_LOOKUP_PRECEDENCE_TESTS
    + COLLATION_LOOKUP_CROSS_COLLECTION_TESTS
    + COLLATION_LOOKUP_INDEX_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_LOOKUP_RESOLUTION_TESTS))
def test_collation_lookup_resolution(database_client, collection, test):
    """Test collation precedence and cross-collection resolution in $lookup joins."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
