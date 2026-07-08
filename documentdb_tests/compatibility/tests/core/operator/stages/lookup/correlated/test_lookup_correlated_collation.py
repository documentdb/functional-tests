"""Tests for $lookup correlated subquery — collation interactions.

Covers command-level collation propagation into sub-pipeline $expr comparisons,
collation through nested lookups, and collation edge cases.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    build_lookup_pipeline,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# --- Section 1: Command-Level Collation in Sub-Pipeline $expr ---

LOOKUP_COLLATION_BASIC_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "collation_strength1_case_insensitive_match",
        docs=[{"_id": 1, "name": "Apple"}],
        foreign_docs=[
            {"_id": 10, "product": "apple"},
            {"_id": 11, "product": "banana"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"n": "$name"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$product", "$$n"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "name": "Apple",
                "joined": [{"_id": 10, "product": "apple"}],
            }
        ],
        msg=(
            "$lookup $expr $eq with collation strength 1 should match"
            " case-insensitively: 'Apple' == 'apple'"
        ),
    ),
    LookupTestCase(
        "no_collation_binary_comparison",
        docs=[{"_id": 1, "name": "Apple"}],
        foreign_docs=[
            {"_id": 10, "product": "apple"},
            {"_id": 11, "product": "Apple"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"n": "$name"},
                    "pipeline": [{"$match": {"$expr": {"$eq": ["$product", "$$n"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "name": "Apple",
                "joined": [{"_id": 11, "product": "Apple"}],
            }
        ],
        msg=(
            "$lookup $expr $eq without collation should use binary"
            " comparison: only exact case match"
        ),
    ),
    LookupTestCase(
        "collation_strength1_lt_ordering",
        docs=[{"_id": 1, "threshold": "b"}],
        foreign_docs=[
            {"_id": 10, "val": "A"},
            {"_id": 11, "val": "C"},
            {"_id": 12, "val": "a"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"thr": "$threshold"},
                    "pipeline": [{"$match": {"$expr": {"$lt": ["$val", "$$thr"]}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "threshold": "b",
                "joined": [
                    {"_id": 10, "val": "A"},
                    {"_id": 12, "val": "a"},
                ],
            }
        ],
        msg=(
            "$lookup $expr $lt with collation strength 1 should order"
            " strings case-insensitively: 'A' and 'a' both < 'b'"
        ),
    ),
]

# --- Section 2: Collation Does NOT Affect Output Values ---

LOOKUP_COLLATION_OUTPUT_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "collation_does_not_alter_addFields_output",
        docs=[{"_id": 1, "label": "Apple"}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$label"},
                    "pipeline": [{"$addFields": {"val": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "label": "Apple",
                "joined": [{"_id": 10, "val": "Apple"}],
            }
        ],
        msg=(
            "$lookup collation should NOT alter $addFields output values"
            " — 'Apple' is stored as 'Apple' regardless of collation"
        ),
    ),
]


def _build_collation_command(collection, test_case, foreign_name, collation):
    """Build aggregate command with collation option."""
    return {
        "aggregate": collection.name,
        "pipeline": build_lookup_pipeline(test_case, foreign_name),
        "cursor": {},
        "collation": collation,
    }


# Tests that require specific collation settings are run with custom commands.
# The parametrized tests below use the default (no collation / binary).
# Collation-specific tests are separate functions below.

LOOKUP_COLLATION_NO_COLLATION_TESTS: list[LookupTestCase] = [
    LOOKUP_COLLATION_BASIC_TESTS[1],  # no_collation_binary_comparison
    LOOKUP_COLLATION_OUTPUT_TESTS[0],  # does_not_alter_output
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_COLLATION_NO_COLLATION_TESTS))
def test_lookup_correlated_collation_binary(collection, test_case: LookupTestCase):
    """Test $lookup correlated subquery with default binary collation."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )


@pytest.mark.aggregate
def test_lookup_correlated_collation_strength1_eq(collection):
    """Test $lookup $expr $eq with collation strength 1 matches case-insensitively."""
    test_case = LOOKUP_COLLATION_BASIC_TESTS[0]
    with setup_lookup(collection, test_case) as foreign_name:
        command = _build_collation_command(
            collection,
            test_case,
            foreign_name,
            {"locale": "en", "strength": 1},
        )
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            msg=test_case.msg,
        )


@pytest.mark.aggregate
def test_lookup_correlated_collation_strength1_lt(collection):
    """Test $lookup $expr $lt with collation strength 1 orders case-insensitively."""
    test_case = LOOKUP_COLLATION_BASIC_TESTS[2]
    with setup_lookup(collection, test_case) as foreign_name:
        command = _build_collation_command(
            collection,
            test_case,
            foreign_name,
            {"locale": "en", "strength": 1},
        )
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            msg=test_case.msg,
        )
