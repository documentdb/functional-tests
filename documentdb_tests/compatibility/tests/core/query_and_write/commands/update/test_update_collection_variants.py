"""Tests for update command with different collection variants."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CappedCollection, ViewCollection

# Property [Collection Type Constraints]: update on a view is rejected;
# update on a capped collection succeeds when document size does not change.
COLLECTION_VARIANT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "update_on_view_errors",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 2}}}],
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="update on a view should be rejected with command-not-supported-on-view error.",
    ),
    CommandTestCase(
        "update_on_capped_collection_same_size",
        target_collection=CappedCollection(),
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 2}}}],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="update on a capped collection should succeed when document size does not change.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLECTION_VARIANT_TESTS))
def test_update_collection_variants(database_client, collection, test: CommandTestCase):
    """Test update command behavior across different collection types."""
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
