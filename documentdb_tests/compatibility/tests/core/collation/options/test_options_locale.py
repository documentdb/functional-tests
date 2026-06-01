"""Tests for locale-specific collation semantics."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Locale Semantic Behavior]: the simple locale produces binary sort
# order, and locale variants using @collation= syntax are accepted and produce
# locale-specific behavior.
COLLATION_LOCALE_SEMANTIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "locale_simple_binary_comparison",
        docs=[{"_id": 1, "x": "b"}, {"_id": 2, "x": "A"}, {"_id": 3, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "simple"},
        },
        expected=[{"_id": 2, "x": "A"}, {"_id": 3, "x": "a"}, {"_id": 1, "x": "b"}],
        msg="aggregate with simple locale should produce binary sort order",
    ),
    CommandTestCase(
        "locale_variant_de_phonebook",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "de@collation=phonebook"},
        },
        expected=[{"_id": 1, "x": "a"}],
        msg="aggregate should accept de@collation=phonebook locale variant",
    ),
    CommandTestCase(
        "locale_variant_zh_unihan",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "zh@collation=unihan"},
        },
        expected=[{"_id": 1, "x": "a"}],
        msg="aggregate should accept zh@collation=unihan locale variant",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_LOCALE_SEMANTIC_TESTS))
def test_collation_locale(database_client, collection, test):
    """Test locale-specific collation semantics."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
