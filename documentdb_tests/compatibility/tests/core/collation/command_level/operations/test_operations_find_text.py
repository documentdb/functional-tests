"""Tests for $text in find with explicit command-level collation."""

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

# Property [Find $text Ignores Explicit Collation]: when a find command
# specifies both a $text filter and an explicit collation, the collation is
# silently ignored for text matching; $text uses the text index's own
# language-based rules instead.
COLLATION_FIND_TEXT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "text_search_ignores_explicit_collation",
        docs=[
            {"_id": 1, "x": "cafe latte"},
            {"_id": 2, "x": "Cafe Mocha"},
            {"_id": 3, "x": "tea"},
        ],
        indexes=[IndexModel([("x", "text")], name="x_text")],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$text": {"$search": "cafe"}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "cafe latte"},
            {"_id": 2, "x": "Cafe Mocha"},
        ],
        msg="$text in find should ignore explicit collation and use text index rules",
    ),
    CommandTestCase(
        "text_search_case_sensitive_ignores_collation",
        docs=[
            {"_id": 1, "x": "cafe latte"},
            {"_id": 2, "x": "Cafe Mocha"},
            {"_id": 3, "x": "CAFE espresso"},
        ],
        indexes=[IndexModel([("x", "text")], name="x_text")],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$text": {"$search": "cafe", "$caseSensitive": True}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "x": "cafe latte"}],
        msg="$text $caseSensitive should not be overridden by explicit collation",
    ),
    CommandTestCase(
        "text_search_diacritic_sensitive_ignores_collation",
        docs=[
            {"_id": 1, "x": "cafe latte"},
            {"_id": 2, "x": "caf\u00e9 mocha"},
            {"_id": 3, "x": "tea"},
        ],
        indexes=[IndexModel([("x", "text")], name="x_text")],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$text": {"$search": "cafe", "$diacriticSensitive": True}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "x": "cafe latte"}],
        msg="$text $diacriticSensitive should not be overridden by explicit collation",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_FIND_TEXT_TESTS))
def test_collation_find_text(database_client, collection, test):
    """Test that $text in find ignores explicit command-level collation."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
