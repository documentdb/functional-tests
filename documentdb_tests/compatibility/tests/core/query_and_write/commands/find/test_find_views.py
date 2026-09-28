"""Tests for find command on views."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    EXPRESSION_ARITY_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import ViewCollection

# Property [View Support]: find works on views and rejects unsupported projection
# operators that cannot be rewritten into the view pipeline.
FIND_VIEW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_returns_documents",
        target_collection=ViewCollection(),
        docs=[
            {"_id": 1, "a": 10, "b": "x"},
            {"_id": 2, "a": 20, "b": "y"},
            {"_id": 3, "a": 30, "b": "z"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"a": {"$gte": 20}},
            "sort": {"_id": 1},
        },
        expected=[{"_id": 2, "a": 20, "b": "y"}, {"_id": 3, "a": 30, "b": "z"}],
        msg="find should return documents from view matching filter.",
    ),
    CommandTestCase(
        "view_with_projection",
        target_collection=ViewCollection(),
        docs=[
            {"_id": 1, "a": 10, "b": "x"},
            {"_id": 2, "a": 20, "b": "y"},
            {"_id": 3, "a": 30, "b": "z"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "projection": {"a": 1},
            "sort": {"_id": 1},
        },
        expected=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}, {"_id": 3, "a": 30}],
        msg="find should support projection on views.",
    ),
    CommandTestCase(
        "view_elemmatch_projection_error",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        command=lambda ctx: {
            "find": ctx.collection,
            "projection": {"a": {"$elemMatch": {"$gt": 1}}},
        },
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="find should reject $elemMatch projection on views.",
    ),
    CommandTestCase(
        "view_slice_projection_error",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        command=lambda ctx: {
            "find": ctx.collection,
            "projection": {"a": {"$slice": 1}},
        },
        error_code=EXPRESSION_ARITY_ERROR,
        msg="find should reject $slice projection on views.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_VIEW_TESTS))
def test_find_views(database_client, collection, test):
    """Test find command on views."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
