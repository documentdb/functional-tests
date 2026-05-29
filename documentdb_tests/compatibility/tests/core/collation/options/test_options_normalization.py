"""Tests for normalization behavior and null acceptance in collation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Normalization Behavior]: normalization:true checks and performs
# normalization for comparison; ICU handles canonical equivalence (NFC/NFD)
# regardless of the flag value; compatibility decomposition (ligatures,
# superscripts) is handled by strength levels not normalization; simple locale
# disables normalization entirely; normalization does NOT modify stored or
# output values.
COLLATION_NORMALIZATION_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "normalization_true_accepted",
        docs=[{"_id": 1, "x": "hello"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": True},
        },
        expected=[{"_id": 1, "x": "hello"}],
        msg="aggregate should accept normalization:true",
    ),
    CommandTestCase(
        "normalization_false_accepted",
        docs=[{"_id": 1, "x": "hello"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "normalization": False},
        },
        expected=[{"_id": 1, "x": "hello"}],
        msg="aggregate should accept normalization:false",
    ),
    CommandTestCase(
        "normalization_canonical_equivalence_regardless_of_flag",
        docs=[
            {"_id": 1, "x": "\u00e9"},  # Precomposed e-acute.
            {"_id": 2, "x": "e\u0301"},  # Decomposed e + combining acute.
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "\u00e9"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3, "normalization": False},
        },
        expected=[
            {"_id": 1, "x": "\u00e9"},
            {"_id": 2, "x": "e\u0301"},
        ],
        msg="ICU should handle canonical equivalence even with normalization:false",
    ),
    CommandTestCase(
        "normalization_compatibility_decomposition_by_strength_not_flag",
        docs=[
            {"_id": 1, "x": "\ufb01"},  # fi ligature (compatibility decomposition).
            {"_id": 2, "x": "fi"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "fi"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3, "normalization": True},
        },
        expected=[{"_id": 2, "x": "fi"}],
        msg="compatibility decomposition not affected by normalization at strength 3",
    ),
    CommandTestCase(
        "normalization_compatibility_decomposition_at_strength_1",
        docs=[
            {"_id": 1, "x": "\ufb01"},  # fi ligature.
            {"_id": 2, "x": "fi"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "fi"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1, "normalization": False},
        },
        expected=[
            {"_id": 1, "x": "\ufb01"},
            {"_id": 2, "x": "fi"},
        ],
        msg="compatibility decomposition handled by strength 1 regardless of normalization",
    ),
    CommandTestCase(
        "normalization_simple_locale_disables",
        docs=[
            {"_id": 1, "x": "\u00e9"},  # Precomposed e-acute.
            {"_id": 2, "x": "e\u0301"},  # Decomposed e + combining acute.
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "\u00e9"}}],
            "cursor": {},
            "collation": {"locale": "simple", "normalization": True},
        },
        expected=[{"_id": 1, "x": "\u00e9"}],
        msg="simple locale should disable normalization entirely (binary comparison)",
    ),
    CommandTestCase(
        "normalization_group_key_preserves_first_encountered",
        docs=[
            {"_id": 1, "x": "e\u0301", "v": 1},  # Decomposed e-acute first.
            {"_id": 2, "x": "\u00e9", "v": 2},  # Precomposed e-acute second.
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": "$x", "vals": {"$push": "$v"}}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3, "normalization": True},
        },
        expected=[{"_id": "e\u0301", "vals": [1, 2]}],
        msg="normalization should not modify stored values; group key preserves first-encountered",
    ),
]

# Property [Normalization Null Acceptance]: null for normalization is treated as
# omitted (uses default false).
COLLATION_NORMALIZATION_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "normalization_null_uses_default_false",
        docs=[
            {"_id": 1, "x": "\u00e9"},
            {"_id": 2, "x": "e\u0301"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "\u00e9"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3, "normalization": None},
        },
        expected=[
            {"_id": 1, "x": "\u00e9"},
            {"_id": 2, "x": "e\u0301"},
        ],
        msg="aggregate should treat null normalization as omitted (default false)",
    ),
]

COLLATION_NORMALIZATION_TESTS: list[CommandTestCase] = (
    COLLATION_NORMALIZATION_BEHAVIOR_TESTS + COLLATION_NORMALIZATION_NULL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_NORMALIZATION_TESTS))
def test_collation_normalization(database_client, collection, test):
    """Test Unicode normalization behavior under collation."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
