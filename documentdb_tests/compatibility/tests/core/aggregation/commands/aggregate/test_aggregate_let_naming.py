"""Tests for aggregate command let variable naming."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Let Variable Naming]: valid let variable names including non-ASCII,
# CJK, emoji, and subsequent character rules.
AGGREGATE_LET_NAMING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "let_field_omitted",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}},
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "x": 10}])},
        },
        msg="aggregate should accept omission of let field (no variables defined)",
    ),
    CommandTestCase(
        "let_null",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "let": None,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept null for let parameter",
    ),
    CommandTestCase(
        "let_empty_doc",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}, "let": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept empty document for let parameter",
    ),
    CommandTestCase(
        "let_simple_variable",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": {"$add": ["$x", "$$myVar"]}}}],
            "cursor": {},
            "let": {"myVar": 5},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "x": 10, "y": 15}])},
        },
        msg="aggregate should resolve let variables in pipeline stages",
    ),
    CommandTestCase(
        "let_name_non_ascii_first_char",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$éval"}}],
            "cursor": {},
            "let": {"éval": 42},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": 42}])},
        },
        msg="aggregate should accept variable name starting with non-ASCII character",
    ),
    CommandTestCase(
        "let_name_cjk_first_char",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$中"}}],
            "cursor": {},
            "let": {"中": "cjk"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": "cjk"}])},
        },
        msg="aggregate should accept variable name starting with CJK character",
    ),
    CommandTestCase(
        "let_name_uppercase_non_ascii",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$Éval"}}],
            "cursor": {},
            "let": {"Éval": 99},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": 99}])},
        },
        msg="aggregate should accept variable name starting with uppercase non-ASCII",
    ),
    CommandTestCase(
        "let_name_emoji_first_char",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$\U0001f600val"}}],
            "cursor": {},
            "let": {"\U0001f600val": "emoji"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": "emoji"}])},
        },
        msg="aggregate should accept variable name starting with emoji character",
    ),
    CommandTestCase(
        "let_name_cyrillic_first_char",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$\u0414val"}}],
            "cursor": {},
            "let": {"\u0414val": "cyrillic"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": "cyrillic"}])},
        },
        msg="aggregate should accept variable name starting with Cyrillic character",
    ),
    CommandTestCase(
        "let_name_subsequent_uppercase",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$aBC"}}],
            "cursor": {},
            "let": {"aBC": "upper"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": "upper"}])},
        },
        msg="aggregate should accept uppercase letters in subsequent variable name positions",
    ),
    CommandTestCase(
        "let_name_subsequent_digits",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$a123"}}],
            "cursor": {},
            "let": {"a123": "digits"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": "digits"}])},
        },
        msg="aggregate should accept digits in subsequent variable name positions",
    ),
    CommandTestCase(
        "let_name_subsequent_underscore",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$a_b"}}],
            "cursor": {},
            "let": {"a_b": "underscore"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": "underscore"}])},
        },
        msg="aggregate should accept underscore in subsequent variable name positions",
    ),
    CommandTestCase(
        "let_name_subsequent_non_ascii",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$aé"}}],
            "cursor": {},
            "let": {"aé": "non_ascii_sub"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": "non_ascii_sub"}])},
        },
        msg="aggregate should accept non-ASCII unicode in subsequent variable name positions",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_LET_NAMING_TESTS))
def test_aggregate_let_naming(database_client, collection, test):
    """Test aggregate let variable naming."""
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
