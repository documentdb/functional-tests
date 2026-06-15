"""
Tests for insert command with different collection variants.

Validates behavior on regular collections, capped collections, and views.
Collection names are derived from the fixture collection name to avoid
collisions under parallel execution.
"""

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

# Property [Collection Variant Acceptance]: insert succeeds on regular and capped
# collections, and is rejected on views.
COLLECTION_VARIANT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "regular_collection",
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 1, "a": 1}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="insert should succeed on regular collection.",
    ),
    CommandTestCase(
        "capped_collection",
        target_collection=CappedCollection(size=1_048_576),
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 1, "a": 1}],
        },
        expected={"ok": 1.0, "n": 1},
        msg="insert should succeed on capped collection.",
    ),
    CommandTestCase(
        "view_rejected",
        target_collection=ViewCollection(),
        docs=[],
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 1}],
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="insert should reject insert into view.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(COLLECTION_VARIANT_TESTS))
def test_insert_collection_variant(database_client, collection, test: CommandTestCase):
    """Test insert behavior across regular, capped, and view collections."""
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
