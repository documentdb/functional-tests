"""Tests for collation effects on facet, redact, and text search stages."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Facet Stage Collation]: collation applies within $facet
# sub-pipelines.
COLLATION_FACET_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "facet_match_strength1",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
            {"_id": 4, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$facet": {"matched": [{"$match": {"x": "apple"}}]}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {
                "matched": [
                    {"_id": 1, "x": "apple"},
                    {"_id": 2, "x": "Apple"},
                    {"_id": 3, "x": "APPLE"},
                ]
            }
        ],
        msg="$facet sub-pipeline $match should use command-level collation",
    ),
    CommandTestCase(
        "facet_sort_strength1",
        docs=[
            {"_id": 1, "x": "banana"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "apple"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$facet": {"sorted": [{"$sort": {"x": 1}}]}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        # Strength 1 treats case variants as equivalent; stable sort preserves
        # insertion order for ties.
        expected=[
            {
                "sorted": [
                    {"_id": 2, "x": "Apple"},
                    {"_id": 3, "x": "apple"},
                    {"_id": 1, "x": "banana"},
                ]
            }
        ],
        msg="$facet sub-pipeline $sort should use command-level collation",
    ),
    CommandTestCase(
        "facet_multiple_pipelines",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$facet": {
                        "matched": [{"$match": {"x": "apple"}}],
                        "sorted": [{"$sort": {"x": 1}}],
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {
                "matched": [
                    {"_id": 1, "x": "apple"},
                    {"_id": 2, "x": "Apple"},
                ],
                "sorted": [
                    {"_id": 1, "x": "apple"},
                    {"_id": 2, "x": "Apple"},
                    {"_id": 3, "x": "banana"},
                ],
            }
        ],
        msg="$facet with multiple sub-pipelines should apply collation to all",
    ),
    CommandTestCase(
        "facet_group_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple", "v": 1},
            {"_id": 2, "x": "Apple", "v": 2},
            {"_id": 3, "x": "banana", "v": 3},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$facet": {
                        "grouped": [
                            {"$sort": {"_id": 1}},
                            {"$group": {"_id": "$x", "total": {"$sum": "$v"}}},
                            {"$sort": {"_id": 1}},
                        ]
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {
                "grouped": [
                    {"_id": "apple", "total": 3},
                    {"_id": "banana", "total": 3},
                ]
            }
        ],
        msg="$facet sub-pipeline $group should use collation for key deduplication",
    ),
]

# Property [Redact Stage Collation]: $redact expressions that involve string
# comparisons ($cmp, $eq) are affected by command-level collation.
COLLATION_REDACT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "redact_eq_strength1_case_insensitive",
        docs=[
            {"_id": 1, "level": "Public", "data": "visible"},
            {"_id": 2, "level": "private", "data": "hidden"},
            {"_id": 3, "level": "PUBLIC", "data": "also visible"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$redact": {
                        "$cond": {
                            "if": {"$eq": ["$level", "public"]},
                            "then": "$$KEEP",
                            "else": "$$PRUNE",
                        }
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "level": "Public", "data": "visible"},
            {"_id": 3, "level": "PUBLIC", "data": "also visible"},
        ],
        msg="$redact with $eq should use collation for case-insensitive comparison",
    ),
    CommandTestCase(
        "redact_cmp_strength1_case_insensitive",
        docs=[
            {"_id": 1, "level": "Public", "data": "visible"},
            {"_id": 2, "level": "private", "data": "hidden"},
            {"_id": 3, "level": "PUBLIC", "data": "also visible"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$redact": {
                        "$cond": {
                            "if": {"$eq": [{"$cmp": ["$level", "public"]}, 0]},
                            "then": "$$KEEP",
                            "else": "$$PRUNE",
                        }
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "level": "Public", "data": "visible"},
            {"_id": 3, "level": "PUBLIC", "data": "also visible"},
        ],
        msg="$redact with $cmp should use collation for case-insensitive comparison",
    ),
]

# Property [Text Search Ignores Collation]: $text search with command-level
# collation does not error but collation is silently ignored, and $text
# $caseSensitive and $diacriticSensitive options are not overridden by
# collation.
COLLATION_TEXT_SEARCH_IGNORED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "text_collation_silently_ignored",
        indexes=[IndexModel([("x", "text")])],
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "CAFE"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"$text": {"$search": "cafe"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "CAFE"},
        ],
        msg="$text search should ignore collation and use text index semantics",
    ),
    CommandTestCase(
        "text_case_sensitive_not_overridden",
        indexes=[IndexModel([("x", "text")])],
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"$text": {"$search": "cafe", "$caseSensitive": True}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "cafe"},
            {"_id": 3, "x": "caf\u00e9"},
        ],
        msg="$text $caseSensitive should not be overridden by collation strength 1",
    ),
    CommandTestCase(
        "text_diacritic_sensitive_not_overridden",
        indexes=[IndexModel([("x", "text")])],
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
            {"_id": 3, "x": "caf\u00e9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$match": {"$text": {"$search": "cafe", "$diacriticSensitive": True}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "Cafe"},
        ],
        msg="$text $diacriticSensitive should not be overridden by collation strength 1",
    ),
]

COLLATION_AGGREGATE_SUBSTAGES_TESTS: list[CommandTestCase] = (
    COLLATION_FACET_TESTS + COLLATION_REDACT_TESTS + COLLATION_TEXT_SEARCH_IGNORED_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_AGGREGATE_SUBSTAGES_TESTS))
def test_collation_aggregate_substages(database_client, collection, test):
    """Test collation effects on sub-pipelines in $facet and $lookup."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
