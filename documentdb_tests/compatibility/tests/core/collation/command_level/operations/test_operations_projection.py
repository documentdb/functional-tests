"""Tests for collation effects on positional $ and $elemMatch projection."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Positional $ Projection with Collation]: the positional $ operator
# projects the first array element that matched the query filter under the
# active collation, so case-insensitive matching projects the correct element.
COLLATION_POSITIONAL_PROJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "positional_projects_collation_matched_element",
        docs=[{"_id": 1, "items": ["Banana", "Apple", "cherry"]}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"items": "apple"},
            "projection": {"items.$": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "items": ["Apple"]}],
        msg="positional $ should project element matched under collation",
    ),
    CommandTestCase(
        "positional_no_collation_binary",
        docs=[{"_id": 1, "items": ["Apple", "apple", "banana"]}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"items": "apple"},
            "projection": {"items.$": 1},
        },
        expected=[{"_id": 1, "items": ["apple"]}],
        msg="positional $ without collation should project binary-matched element",
    ),
    CommandTestCase(
        "positional_accent_insensitive",
        docs=[{"_id": 1, "items": ["tea", "caf\u00e9", "juice"]}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"items": "cafe"},
            "projection": {"items.$": 1},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "items": ["caf\u00e9"]}],
        msg="positional $ with strength 1 should project accent-variant match",
    ),
]

# Property [$elemMatch Projection with Collation]: the $elemMatch projection
# operator uses the active collation to determine which array element to
# project, enabling case-insensitive element selection.
COLLATION_ELEMMATCH_PROJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "elemmatch_proj_case_insensitive",
        docs=[{"_id": 1, "items": [{"v": "Banana"}, {"v": "Apple"}, {"v": "cherry"}]}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"_id": 1},
            "projection": {"items": {"$elemMatch": {"v": "apple"}}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "items": [{"v": "Apple"}]}],
        msg="$elemMatch projection with strength 2 should match case-insensitively",
    ),
    CommandTestCase(
        "elemmatch_proj_no_collation_binary",
        docs=[{"_id": 1, "items": [{"v": "Apple"}, {"v": "apple"}, {"v": "banana"}]}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"_id": 1},
            "projection": {"items": {"$elemMatch": {"v": "apple"}}},
        },
        expected=[{"_id": 1, "items": [{"v": "apple"}]}],
        msg="$elemMatch projection without collation should use binary comparison",
    ),
    CommandTestCase(
        "elemmatch_proj_comparison_operator",
        docs=[{"_id": 1, "items": [{"v": "apple"}, {"v": "Banana"}, {"v": "cherry"}]}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"_id": 1},
            "projection": {"items": {"$elemMatch": {"v": {"$gte": "banana"}}}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "items": [{"v": "Banana"}]}],
        msg="$elemMatch projection with $gte should use collation",
    ),
]

COLLATION_PROJECTION_TESTS = (
    COLLATION_POSITIONAL_PROJECTION_TESTS + COLLATION_ELEMMATCH_PROJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_PROJECTION_TESTS))
def test_collation_projection(database_client, collection, test):
    """Test collation effects on array projection operators."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
