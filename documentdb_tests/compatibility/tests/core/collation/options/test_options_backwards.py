"""Tests for backwards sort ordering behavior in collation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Backwards Sort Ordering]: backwards:true reverses secondary
# (diacritic) comparison direction so strings with diacritics sort from back of
# string; backwards:false (default) compares diacritics front to back;
# backwards only affects ordering comparisons, not equality.
COLLATION_BACKWARDS_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "backwards_false_sort_diacritics_front_to_back",
        docs=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "fr", "strength": 2, "backwards": False},
        },
        expected=[
            {"_id": 1, "x": "cote"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        msg="backwards:false should compare diacritics front to back",
    ),
    CommandTestCase(
        "backwards_true_sort_diacritics_back_to_front",
        docs=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "fr", "strength": 2, "backwards": True},
        },
        expected=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        msg="backwards:true should compare diacritics back to front",
    ),
    CommandTestCase(
        "backwards_true_lt_comparison",
        docs=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$lt": "c\u00f4te"}}}, {"$sort": {"_id": 1}}],
            "cursor": {},
            "collation": {"locale": "fr", "strength": 2, "backwards": True},
        },
        expected=[{"_id": 1, "x": "cote"}],
        msg="backwards:true should affect $lt ordering",
    ),
    CommandTestCase(
        "backwards_false_lt_comparison",
        docs=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$lt": "c\u00f4te"}}}, {"$sort": {"_id": 1}}],
            "cursor": {},
            "collation": {"locale": "fr", "strength": 2, "backwards": False},
        },
        expected=[{"_id": 1, "x": "cote"}, {"_id": 3, "x": "cot\u00e9"}],
        msg="backwards:false should affect $lt ordering differently than backwards:true",
    ),
    CommandTestCase(
        "backwards_true_eq_not_affected",
        docs=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "cot\u00e9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "cote"}}],
            "cursor": {},
            "collation": {"locale": "fr", "strength": 2, "backwards": True},
        },
        expected=[{"_id": 1, "x": "cote"}],
        msg="backwards:true should not affect $eq matching",
    ),
    CommandTestCase(
        "backwards_true_in_not_affected",
        docs=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "cot\u00e9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": {"$in": ["cote"]}}}],
            "cursor": {},
            "collation": {"locale": "fr", "strength": 2, "backwards": True},
        },
        expected=[{"_id": 1, "x": "cote"}],
        msg="backwards:true should not affect $in matching",
    ),
    CommandTestCase(
        "backwards_fr_ca_default_true",
        docs=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "fr_CA", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        msg="fr_CA locale should default to backwards:true when field is omitted",
    ),
    CommandTestCase(
        "backwards_default_false_non_fr_ca",
        docs=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "fr", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "cote"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        msg="omitting backwards for non-fr_CA locale should default to backwards:false",
    ),
    CommandTestCase(
        "backwards_fr_ca_explicit_false",
        docs=[
            {"_id": 1, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$sort": {"x": 1}}],
            "cursor": {},
            "collation": {"locale": "fr_CA", "strength": 2, "backwards": False},
        },
        expected=[
            {"_id": 1, "x": "cote"},
            {"_id": 3, "x": "cot\u00e9"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 4, "x": "c\u00f4t\u00e9"},
        ],
        msg="fr_CA with explicit backwards:false should override the locale default",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_BACKWARDS_BEHAVIOR_TESTS))
def test_collation_backwards(database_client, collection, test):
    """Test backwards collation option for accent ordering."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
