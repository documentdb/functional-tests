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

# Property [Foreign Collation Ignored Across Forms]: the foreign collection's
# own default collation is never used for the join in any correlated form;
# matching follows the source collection default, or binary when the source has
# none. Cases use a case-insensitive foreign default so "ignored" is observable.
COLLATION_LOOKUP_FOREIGN_IGNORED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "equality_foreign_default_ignored_falls_back_to_binary",
        siblings=[
            SiblingCollection(
                suffix="_foreign",
                collation={"locale": "en", "strength": 1},
                docs=[{"_id": 10, "x": "Apple"}],
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
                }
            ],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": "apple", "matched": []}],
        msg="equality $lookup should ignore a case-insensitive foreign default and "
        "match by binary, so apple does not match Apple",
    ),
    CommandTestCase(
        "equality_source_default_governs_over_foreign",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        siblings=[
            SiblingCollection(
                suffix="_foreign",
                collation={"locale": "fr", "strength": 3},
                docs=[{"_id": 10, "x": "Apple"}],
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
                }
            ],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": "apple", "matched": [{"_id": 10, "x": "Apple"}]}],
        msg="equality $lookup should use the source default over a differing "
        "foreign default, so apple matches Apple",
    ),
    CommandTestCase(
        "verbose_foreign_default_ignored_falls_back_to_binary",
        siblings=[
            SiblingCollection(
                suffix="_foreign",
                collation={"locale": "en", "strength": 1},
                docs=[{"_id": 10, "x": "Apple"}],
            ),
        ],
        docs=[{"_id": 1, "x": "apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection + "_foreign",
                        "let": {"p": "$x"},
                        "pipeline": [{"$match": {"$expr": {"$eq": ["$x", "$$p"]}}}],
                        "as": "matched",
                    }
                }
            ],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": "apple", "matched": []}],
        msg="verbose $lookup sub-pipeline should ignore a case-insensitive foreign "
        "default and match by binary",
    ),
    CommandTestCase(
        "verbose_source_default_governs_over_foreign",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        siblings=[
            SiblingCollection(
                suffix="_foreign",
                collation={"locale": "fr", "strength": 3},
                docs=[{"_id": 10, "x": "Apple"}],
            ),
        ],
        docs=[{"_id": 1, "x": "apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection + "_foreign",
                        "let": {"p": "$x"},
                        "pipeline": [{"$match": {"$expr": {"$eq": ["$x", "$$p"]}}}],
                        "as": "matched",
                    }
                }
            ],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": "apple", "matched": [{"_id": 10, "x": "Apple"}]}],
        msg="verbose $lookup sub-pipeline should use the source default over a "
        "differing foreign default",
    ),
    CommandTestCase(
        "concise_source_default_governs_over_foreign",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        siblings=[
            SiblingCollection(
                suffix="_foreign",
                collation={"locale": "fr", "strength": 3},
                docs=[{"_id": 10, "x": "Apple"}],
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
                        "pipeline": [{"$match": {}}],
                        "as": "matched",
                    }
                }
            ],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": "apple", "matched": [{"_id": 10, "x": "Apple"}]}],
        msg="concise $lookup should use the source default over a differing foreign "
        "default in its equality prefilter",
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

# Property [Nested Foreign Collation Across Collections and Syntaxes]: in nested
# lookups spanning multiple distinct collections, the source collection default
# governs matching at every level and each foreign default is ignored, whatever
# lookup syntax each level uses. These use distinct collections rather than a
# self-join, and mix syntaxes across levels.
COLLATION_LOOKUP_NESTED_FOREIGN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "nested_verbose_multi_collection_source_governs",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        siblings=[
            SiblingCollection(
                suffix="_a",
                collation={"locale": "fr", "strength": 3},
                docs=[{"_id": 10, "x": "apple", "y": "Banana"}],
            ),
            SiblingCollection(
                suffix="_b",
                collation={"locale": "fr", "strength": 3},
                docs=[{"_id": 20, "z": "banana"}],
            ),
        ],
        docs=[{"_id": 1, "x": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection + "_a",
                        "let": {"p": "$x"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$x", "$$p"]}}},
                            {
                                "$lookup": {
                                    "from": ctx.collection + "_b",
                                    "let": {"q": "$y"},
                                    "pipeline": [{"$match": {"$expr": {"$eq": ["$z", "$$q"]}}}],
                                    "as": "inner",
                                }
                            },
                        ],
                        "as": "m",
                    }
                }
            ],
            "cursor": {},
        },
        expected=[
            {
                "_id": 1,
                "x": "Apple",
                "m": [
                    {
                        "_id": 10,
                        "x": "apple",
                        "y": "Banana",
                        "inner": [{"_id": 20, "z": "banana"}],
                    }
                ],
            }
        ],
        msg="nested verbose lookups over distinct collections should use the source "
        "default at both levels and ignore each foreign default",
    ),
    CommandTestCase(
        "nested_verbose_base_standard_inner_source_governs",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        siblings=[
            SiblingCollection(
                suffix="_a",
                collation={"locale": "fr", "strength": 3},
                docs=[{"_id": 10, "x": "apple", "y": "Banana"}],
            ),
            SiblingCollection(
                suffix="_b",
                collation={"locale": "fr", "strength": 3},
                docs=[{"_id": 20, "z": "banana"}],
            ),
        ],
        docs=[{"_id": 1, "x": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection + "_a",
                        "let": {"p": "$x"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$x", "$$p"]}}},
                            {
                                "$lookup": {
                                    "from": ctx.collection + "_b",
                                    "localField": "y",
                                    "foreignField": "z",
                                    "as": "inner",
                                }
                            },
                        ],
                        "as": "m",
                    }
                }
            ],
            "cursor": {},
        },
        expected=[
            {
                "_id": 1,
                "x": "Apple",
                "m": [
                    {
                        "_id": 10,
                        "x": "apple",
                        "y": "Banana",
                        "inner": [{"_id": 20, "z": "banana"}],
                    }
                ],
            }
        ],
        msg="a verbose base with a standard inner lookup over distinct collections "
        "should apply the source default across both syntaxes",
    ),
    CommandTestCase(
        "nested_concise_base_uncorrelated_inner_source_governs",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        siblings=[
            SiblingCollection(
                suffix="_a",
                collation={"locale": "fr", "strength": 3},
                docs=[{"_id": 10, "x": "apple"}],
            ),
            SiblingCollection(
                suffix="_b",
                collation={"locale": "fr", "strength": 3},
                docs=[{"_id": 20, "w": "HELLO"}],
            ),
        ],
        docs=[{"_id": 1, "x": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection + "_a",
                        "localField": "x",
                        "foreignField": "x",
                        "pipeline": [
                            {
                                "$lookup": {
                                    "from": ctx.collection + "_b",
                                    "pipeline": [{"$match": {"w": "hello"}}],
                                    "as": "inner",
                                }
                            }
                        ],
                        "as": "m",
                    }
                }
            ],
            "cursor": {},
        },
        expected=[
            {
                "_id": 1,
                "x": "Apple",
                "m": [{"_id": 10, "x": "apple", "inner": [{"_id": 20, "w": "HELLO"}]}],
            }
        ],
        msg="a concise base with an uncorrelated inner lookup over distinct "
        "collections should apply the source default across both syntaxes",
    ),
]

COLLATION_LOOKUP_RESOLUTION_TESTS: list[CommandTestCase] = (
    COLLATION_LOOKUP_PRECEDENCE_TESTS
    + COLLATION_LOOKUP_FOREIGN_IGNORED_TESTS
    + COLLATION_LOOKUP_INDEX_TESTS
    + COLLATION_LOOKUP_NESTED_FOREIGN_TESTS
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
