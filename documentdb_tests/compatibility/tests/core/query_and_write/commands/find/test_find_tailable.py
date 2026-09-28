"""Tests for find command tailable cursors on capped collections."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CappedCollection

# Property [Tailable Cursors]: find supports tailable cursors on capped collections
# and rejects tailable/awaitData on non-capped collections.
FIND_TAILABLE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "capped_collection",
        target_collection=CappedCollection(size=10_000),
        docs=[{"_id": i, "val": i * 10} for i in range(5)],
        command=lambda ctx: {"find": ctx.collection, "sort": {"$natural": 1}},
        expected=[{"_id": i, "val": i * 10} for i in range(5)],
        msg="find should return capped collection docs in insertion order.",
    ),
    CommandTestCase(
        "tailable_on_capped",
        target_collection=CappedCollection(size=10_000),
        docs=[{"_id": i, "val": i * 10} for i in range(5)],
        command=lambda ctx: {"find": ctx.collection, "tailable": True, "batchSize": 5},
        expected=[{"_id": i, "val": i * 10} for i in range(5)],
        msg="find should accept tailable cursor on capped collection.",
    ),
    CommandTestCase(
        "tailable_on_non_capped_error",
        docs=[{"_id": 1}],
        command=lambda ctx: {"find": ctx.collection, "tailable": True},
        error_code=BAD_VALUE_ERROR,
        msg="find should reject tailable cursor on non-capped collection.",
    ),
    CommandTestCase(
        "await_data_requires_tailable",
        docs=[{"_id": 1}],
        command=lambda ctx: {"find": ctx.collection, "awaitData": True},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="find should reject awaitData without tailable.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_TAILABLE_TESTS))
def test_find_tailable(database_client, collection, test):
    """Test find command tailable cursor behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
