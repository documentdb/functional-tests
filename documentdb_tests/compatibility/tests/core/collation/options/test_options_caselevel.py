"""Tests for caseLevel interaction with strength and null acceptance."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [caseLevel Interaction with Strength]: caseLevel:true adds a case
# distinction at strength 1 and 2 (where case is normally ignored), while
# caseLevel:false preserves the default behavior; at strength 3+ caseLevel:true
# has no additional effect.
COLLATION_CASELEVEL_STRENGTH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "caselevel_true_strength1_match_lowercase",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "\u00e1"},
            {"_id": 4, "x": "\u00c1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "a"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1, "caseLevel": True},
        },
        expected=[{"_id": 1, "x": "a"}, {"_id": 3, "x": "\u00e1"}],
        msg="caseLevel:true strength 1 should match same-case ignoring diacritics",
    ),
    CommandTestCase(
        "caselevel_true_strength1_match_uppercase",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "\u00e1"},
            {"_id": 4, "x": "\u00c1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "A"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1, "caseLevel": True},
        },
        expected=[{"_id": 2, "x": "A"}, {"_id": 4, "x": "\u00c1"}],
        msg="caseLevel:true strength 1 should match uppercase ignoring diacritics",
    ),
    CommandTestCase(
        "caselevel_true_strength2_distinguishes_case_and_diacritics",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "\u00e1"},
            {"_id": 4, "x": "\u00c1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "a"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2, "caseLevel": True},
        },
        expected=[{"_id": 1, "x": "a"}],
        msg="caseLevel:true strength 2 should distinguish both case and diacritics",
    ),
    CommandTestCase(
        "caselevel_false_strength1_no_case_distinction",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "\u00e1"},
            {"_id": 4, "x": "\u00c1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "a"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1, "caseLevel": False},
        },
        expected=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "\u00e1"},
            {"_id": 4, "x": "\u00c1"},
        ],
        msg="caseLevel:false strength 1 should not distinguish case",
    ),
    CommandTestCase(
        "caselevel_false_strength2_no_case_distinction",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "\u00e1"},
            {"_id": 4, "x": "\u00c1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "a"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2, "caseLevel": False},
        },
        expected=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "A"}],
        msg="caseLevel:false strength 2 should ignore case but distinguish diacritics",
    ),
    CommandTestCase(
        "caselevel_true_strength3_no_additional_effect",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
            {"_id": 3, "x": "\u00e1"},
            {"_id": 4, "x": "\u00c1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "a"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 3, "caseLevel": True},
        },
        expected=[{"_id": 1, "x": "a"}],
        msg="caseLevel:true at strength 3 should have no additional effect",
    ),
    CommandTestCase(
        "caselevel_true_strength1_sort_lowercase_before_uppercase",
        docs=[
            {"_id": 1, "x": "B"},
            {"_id": 2, "x": "a"},
            {"_id": 3, "x": "A"},
            {"_id": 4, "x": "b"},
            {"_id": 5, "x": "\u00e1"},
            {"_id": 6, "x": "\u00c1"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1, "caseLevel": True},
        },
        expected=[
            {"_id": 2, "x": "a"},
            {"_id": 5, "x": "\u00e1"},
            {"_id": 3, "x": "A"},
            {"_id": 6, "x": "\u00c1"},
            {"_id": 4, "x": "b"},
            {"_id": 1, "x": "B"},
        ],
        msg="caseLevel:true strength 1 sort should place lowercase before uppercase",
    ),
]

# Property [caseLevel Null Acceptance]: null for caseLevel is treated as
# omitted, using the default value of false.
COLLATION_CASELEVEL_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "caselevel_null_uses_default_false",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "A"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "a"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1, "caseLevel": None},
        },
        expected=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "A"}],
        msg="aggregate should treat null caseLevel as omitted (default false)",
    ),
]

COLLATION_CASELEVEL_TESTS: list[CommandTestCase] = (
    COLLATION_CASELEVEL_STRENGTH_TESTS + COLLATION_CASELEVEL_NULL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_CASELEVEL_TESTS))
def test_collation_caselevel(database_client, collection, test):
    """Test caseLevel collation option behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
