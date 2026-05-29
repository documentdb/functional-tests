"""Tests for write rejection on views."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import ViewCollection

# Property [Write Rejection]: insert, update, delete, and findAndModify
# on a view are rejected with the command-not-supported-on-view error.
VIEWS_WRITE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "insert_rejected",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 99, "x": 99}],
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="insert on a view should be rejected",
    ),
    CommandTestCase(
        "update_rejected",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 99}}}],
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="update on a view should be rejected",
    ),
    CommandTestCase(
        "delete_rejected",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": 1}, "limit": 1}],
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="delete on a view should be rejected",
    ),
    CommandTestCase(
        "find_and_modify_rejected",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "findAndModify": ctx.collection,
            "query": {"_id": 1},
            "update": {"$set": {"x": 99}},
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="findAndModify on a view should be rejected",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VIEWS_WRITE_REJECTION_TESTS))
def test_views_write_rejection(database_client, collection, test):
    """Test write operations are rejected on views."""
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
