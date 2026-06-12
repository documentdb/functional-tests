"""Tests for collation semantics in the count command.

Tests collation-specific behaviors (strength levels, accent handling) that go
beyond basic wiring validation covered in the count command tests.
"""

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

# Property [Count Strength Semantics]: different strength levels produce
# different matching behavior - strength 1 ignores accents and case,
# strength 3 is case-sensitive.
COLLATION_COUNT_STRENGTH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "strength1_accent_insensitive",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "caf\u00e9"},
            {"_id": 3, "x": "other"},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"x": "cafe"},
            "collation": {"locale": "en", "strength": 1},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count with strength 1 should match accent-insensitively",
    ),
    CommandTestCase(
        "strength3_case_sensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"x": "apple"},
            "collation": {"locale": "en", "strength": 3},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count with strength 3 should match case-sensitively",
    ),
    CommandTestCase(
        "no_query_counts_all",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"n": 3, "ok": 1.0},
        msg="count without query should return total count regardless of collation",
    ),
]

# Property [Count Collection Default Collation]: when no explicit collation is
# specified, the count command uses the collection's default collation.
COLLATION_COUNT_DEFAULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_default_case_insensitive",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"x": "apple"},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count should use collection default collation when none specified",
    ),
    CommandTestCase(
        "explicit_overrides_collection_default",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 1}}),
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"x": "apple"},
            "collation": {"locale": "en", "strength": 3},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count with explicit collation should override collection default",
    ),
]

COLLATION_COUNT_TESTS = COLLATION_COUNT_STRENGTH_TESTS + COLLATION_COUNT_DEFAULT_TESTS


@pytest.mark.parametrize("test", pytest_params(COLLATION_COUNT_TESTS))
def test_collation_count(database_client, collection, test):
    """Test collation strength semantics in the count command."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
