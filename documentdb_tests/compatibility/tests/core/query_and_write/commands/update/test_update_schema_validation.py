"""Tests for update command interaction with schema validation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import DOCUMENT_VALIDATION_FAILURE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

_INT_X_VALIDATOR = {
    "validator": {
        "$jsonSchema": {
            "required": ["x"],
            "properties": {"x": {"bsonType": "int"}},
        }
    }
}

# Property [Schema Validation]: update respects the collection validator —
# violations are rejected by default and permitted only with
# bypassDocumentValidation:true.
SCHEMA_VALIDATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "update_violating_validation_fails",
        target_collection=CustomCollection(options=_INT_X_VALIDATOR),
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": "not_int"}}}],
        },
        error_code=DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="update should fail when the result violates the collection validator.",
    ),
    CommandTestCase(
        "update_violating_validation_succeeds_with_bypass",
        target_collection=CustomCollection(options=_INT_X_VALIDATOR),
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": "not_int"}}}],
            "bypassDocumentValidation": True,
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg=(
            "update with bypassDocumentValidation:true should succeed"
            " even if the result violates the validator."
        ),
    ),
    CommandTestCase(
        "update_passing_validation_succeeds",
        target_collection=CustomCollection(options=_INT_X_VALIDATOR),
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 42}}}],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="update should succeed when the result satisfies the collection validator.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SCHEMA_VALIDATION_TESTS))
def test_update_schema_validation(database_client, collection, test: CommandTestCase):
    """Test update command respects collection schema validation."""
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
