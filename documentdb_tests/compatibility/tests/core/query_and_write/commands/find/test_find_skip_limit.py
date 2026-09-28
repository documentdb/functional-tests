"""Tests for find command skip and limit behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [{"_id": i, "val": i * 10} for i in range(10)]


# Property [Skip and Limit]: find applies skip after sort and limit after skip,
# returning the correct pagination window.
FIND_SKIP_LIMIT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "skip_zero",
        docs=DOCS,
        command=lambda ctx: {"find": ctx.collection, "skip": 0, "sort": {"_id": 1}},
        expected=DOCS,
        msg="find should return all documents when skip=0.",
    ),
    CommandTestCase(
        "skip_n",
        docs=DOCS,
        command=lambda ctx: {"find": ctx.collection, "skip": 3, "sort": {"_id": 1}},
        expected=DOCS[3:],
        msg="find should skip first N documents.",
    ),
    CommandTestCase(
        "skip_exceeds_collection",
        docs=DOCS,
        command=lambda ctx: {"find": ctx.collection, "skip": 100, "sort": {"_id": 1}},
        expected=[],
        msg="find should return empty when skip exceeds collection size.",
    ),
    CommandTestCase(
        "limit_zero",
        docs=DOCS,
        command=lambda ctx: {"find": ctx.collection, "limit": 0, "sort": {"_id": 1}},
        expected=DOCS,
        msg="find should return all documents when limit=0.",
    ),
    CommandTestCase(
        "limit_one",
        docs=DOCS,
        command=lambda ctx: {"find": ctx.collection, "limit": 1, "sort": {"_id": 1}},
        expected=[DOCS[0]],
        msg="find should return exactly 1 document when limit=1.",
    ),
    CommandTestCase(
        "limit_n",
        docs=DOCS,
        command=lambda ctx: {"find": ctx.collection, "limit": 5, "sort": {"_id": 1}},
        expected=DOCS[:5],
        msg="find should return at most N documents.",
    ),
    CommandTestCase(
        "skip_and_limit_pagination",
        docs=DOCS,
        command=lambda ctx: {"find": ctx.collection, "skip": 3, "limit": 4, "sort": {"_id": 1}},
        expected=DOCS[3:7],
        msg="find should apply skip then limit for pagination.",
    ),
    CommandTestCase(
        "sort_skip_limit_order",
        docs=[
            {"_id": 1, "a": 50},
            {"_id": 2, "a": 10},
            {"_id": 3, "a": 30},
            {"_id": 4, "a": 20},
            {"_id": 5, "a": 40},
        ],
        command=lambda ctx: {"find": ctx.collection, "sort": {"a": 1}, "skip": 1, "limit": 2},
        expected=[{"_id": 4, "a": 20}, {"_id": 3, "a": 30}],
        msg="find should apply sort before skip before limit.",
    ),
    CommandTestCase(
        "skip_plus_limit_exceeds_count",
        docs=DOCS[:5],
        command=lambda ctx: {"find": ctx.collection, "skip": 3, "limit": 10, "sort": {"_id": 1}},
        expected=DOCS[3:5],
        msg="find should return remaining docs when skip + limit exceeds total.",
    ),
    CommandTestCase(
        "skip_equals_total",
        docs=DOCS[:5],
        command=lambda ctx: {"find": ctx.collection, "skip": 5, "limit": 5, "sort": {"_id": 1}},
        expected=[],
        msg="find should return empty when skip equals collection size.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_SKIP_LIMIT_TESTS))
def test_find_skip_limit(database_client, collection, test):
    """Test find command skip and limit behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
