"""Tests for alternate and maxVariable behavior and null acceptance in collation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Alternate and MaxVariable Behavior]: alternate:"shifted" makes
# whitespace and punctuation ignorable at strength <= 3 (distinguished at
# strength 4+), maxVariable controls which characters are ignorable, and symbol
# characters are never ignorable regardless of settings.
COLLATION_ALTERNATE_MAXVARIABLE_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "alternate_non_ignorable_default",
        docs=[
            {"_id": 1, "x": "a b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a-b"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {"locale": "en", "alternate": "non-ignorable"},
        },
        expected=[{"_id": 2, "x": "ab"}],
        msg="alternate non-ignorable should treat whitespace and punctuation as base characters",
    ),
    CommandTestCase(
        "alternate_shifted_strength3_punct",
        docs=[
            {"_id": 1, "x": "a b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a-b"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "alternate": "shifted",
                "strength": 3,
                "maxVariable": "punct",
            },
        },
        expected=[
            {"_id": 1, "x": "a b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a-b"},
        ],
        msg="alternate shifted with maxVariable punct should ignore whitespace and punctuation",
    ),
    CommandTestCase(
        "alternate_shifted_strength3_space",
        docs=[
            {"_id": 1, "x": "a b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a-b"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "alternate": "shifted",
                "strength": 3,
                "maxVariable": "space",
            },
        },
        expected=[{"_id": 1, "x": "a b"}, {"_id": 2, "x": "ab"}],
        msg="alternate shifted with maxVariable space should ignore only whitespace",
    ),
    CommandTestCase(
        "alternate_shifted_strength4_distinguished",
        docs=[
            {"_id": 1, "x": "a b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a-b"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "alternate": "shifted",
                "strength": 4,
                "maxVariable": "punct",
            },
        },
        expected=[{"_id": 2, "x": "ab"}],
        msg="alternate shifted at strength 4 should distinguish punctuation and whitespace",
    ),
    CommandTestCase(
        "maxvariable_no_effect_with_non_ignorable",
        docs=[
            {"_id": 1, "x": "a b"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a-b"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "alternate": "non-ignorable",
                "maxVariable": "punct",
            },
        },
        expected=[{"_id": 2, "x": "ab"}],
        msg="maxVariable should have no effect when alternate is non-ignorable",
    ),
    CommandTestCase(
        "nbsp_classified_as_punctuation",
        docs=[
            {"_id": 1, "x": "a\u00a0b"},
            {"_id": 2, "x": "ab"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "alternate": "shifted",
                "strength": 3,
                "maxVariable": "space",
            },
        },
        expected=[{"_id": 2, "x": "ab"}],
        msg="NBSP (U+00A0) should not be ignorable with maxVariable space (classified as punct)",
    ),
    CommandTestCase(
        "nbsp_ignorable_with_punct",
        docs=[
            {"_id": 1, "x": "a\u00a0b"},
            {"_id": 2, "x": "ab"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "alternate": "shifted",
                "strength": 3,
                "maxVariable": "punct",
            },
        },
        expected=[{"_id": 1, "x": "a\u00a0b"}, {"_id": 2, "x": "ab"}],
        msg="NBSP (U+00A0) should be ignorable with maxVariable punct",
    ),
    CommandTestCase(
        "zero_width_ignorable_strength4_non_ignorable",
        docs=[
            {"_id": 1, "x": "a\u200bb"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a\u200db"},
            {"_id": 4, "x": "a\ufeffb"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 4, "alternate": "non-ignorable"},
        },
        expected=[
            {"_id": 1, "x": "a\u200bb"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a\u200db"},
            {"_id": 4, "x": "a\ufeffb"},
        ],
        msg="zero-width chars should be ignorable at strength 4 regardless of alternate",
    ),
    CommandTestCase(
        "zero_width_ignorable_strength4_shifted",
        docs=[
            {"_id": 1, "x": "a\u200bb"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a\u200db"},
            {"_id": 4, "x": "a\ufeffb"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 4, "alternate": "shifted"},
        },
        expected=[
            {"_id": 1, "x": "a\u200bb"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a\u200db"},
            {"_id": 4, "x": "a\ufeffb"},
        ],
        msg="zero-width chars should be ignorable at strength 4 even with alternate shifted",
    ),
    CommandTestCase(
        "zero_width_distinguished_strength5",
        docs=[
            {"_id": 1, "x": "a\u200bb"},
            {"_id": 2, "x": "ab"},
            {"_id": 3, "x": "a\u200db"},
            {"_id": 4, "x": "a\ufeffb"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 5, "alternate": "non-ignorable"},
        },
        expected=[{"_id": 2, "x": "ab"}],
        msg="zero-width chars should be distinguished at strength 5",
    ),
    CommandTestCase(
        "all_punct_whitespace_equals_empty",
        docs=[
            {"_id": 1, "x": "..."},
            {"_id": 2, "x": "   "},
            {"_id": 3, "x": ""},
            {"_id": 4, "x": "-_-"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": ""}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "alternate": "shifted",
                "strength": 3,
                "maxVariable": "punct",
            },
        },
        expected=[
            {"_id": 1, "x": "..."},
            {"_id": 2, "x": "   "},
            {"_id": 3, "x": ""},
            {"_id": 4, "x": "-_-"},
        ],
        msg="all-punct/whitespace strings should equal empty string with shifted+punct",
    ),
    CommandTestCase(
        "null_byte_ignorable_shifted_punct",
        docs=[
            {"_id": 1, "x": "a\x00b"},
            {"_id": 2, "x": "ab"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "alternate": "shifted",
                "strength": 3,
                "maxVariable": "punct",
            },
        },
        expected=[{"_id": 1, "x": "a\x00b"}, {"_id": 2, "x": "ab"}],
        msg="null byte (U+0000) should be ignorable with alternate shifted and maxVariable punct",
    ),
    CommandTestCase(
        "symbols_never_ignorable",
        docs=[
            {"_id": 1, "x": "a$b"},
            {"_id": 2, "x": "a+b"},
            {"_id": 3, "x": "a=b"},
            {"_id": 4, "x": "a\u20acb"},
            {"_id": 5, "x": "ab"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "alternate": "shifted",
                "strength": 3,
                "maxVariable": "punct",
            },
        },
        expected=[{"_id": 5, "x": "ab"}],
        msg="symbol characters (dollar, plus, equals, currency) should never be ignorable",
    ),
]

# Property [Alternate and MaxVariable Null Acceptance]: null for alternate is
# treated as omitted (default "non-ignorable"), and null for maxVariable is
# treated as omitted (default "punct").
COLLATION_ALTERNATE_MAXVARIABLE_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "alternate_null_uses_default_non_ignorable",
        docs=[{"_id": 1, "x": "a b"}, {"_id": 2, "x": "ab"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {"locale": "en", "alternate": None},
        },
        expected=[{"_id": 2, "x": "ab"}],
        msg="aggregate should treat null alternate as omitted (default non-ignorable)",
    ),
    CommandTestCase(
        "maxvariable_null_uses_default_punct",
        docs=[{"_id": 1, "x": "a.b"}, {"_id": 2, "x": "ab"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "ab"}}],
            "cursor": {},
            "collation": {
                "locale": "en",
                "alternate": "shifted",
                "strength": 3,
                "maxVariable": None,
            },
        },
        expected=[{"_id": 1, "x": "a.b"}, {"_id": 2, "x": "ab"}],
        msg="aggregate should treat null maxVariable as omitted (default punct)",
    ),
]

COLLATION_ALTERNATE_TESTS: list[CommandTestCase] = (
    COLLATION_ALTERNATE_MAXVARIABLE_BEHAVIOR_TESTS + COLLATION_ALTERNATE_MAXVARIABLE_NULL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_ALTERNATE_TESTS))
def test_collation_alternate(database_client, collection, test):
    """Test alternate and maxVariable collation options."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
