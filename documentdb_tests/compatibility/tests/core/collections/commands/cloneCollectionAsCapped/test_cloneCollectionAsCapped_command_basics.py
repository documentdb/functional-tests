"""Tests for cloneCollectionAsCapped command basic behavior."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Response Format]: the command returns {'ok': 1.0} with no
# additional fields on success.
RESPONSE_FORMAT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "success_response",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="Should return ok:1.0",
    ),
]

# Property [Unrecognized Fields]: unrecognized top-level command fields
# are silently ignored.
UNRECOGNIZED_FIELDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "single_unknown_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "unknownField": 1,
        },
        expected={"ok": 1.0},
        msg="Single unrecognized field should be silently ignored",
    ),
    CommandTestCase(
        "multiple_unknown_fields",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "foo": "bar",
            "baz": [1, 2, 3],
        },
        expected={"ok": 1.0},
        msg="Multiple unrecognized fields should be silently ignored",
    ),
    CommandTestCase(
        "unknown_field_with_null_value",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "unknownField": None,
        },
        expected={"ok": 1.0},
        msg="Unrecognized field with null value should be silently ignored",
    ),
    CommandTestCase(
        "unknown_field_with_object_value",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "unknownField": {"nested": "doc"},
        },
        expected={"ok": 1.0},
        msg="Unrecognized field with object value should be silently ignored",
    ),
]

COMMAND_BASICS_TESTS: list[CommandTestCase] = RESPONSE_FORMAT_TESTS + UNRECOGNIZED_FIELDS_TESTS


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMMAND_BASICS_TESTS))
def test_clone_collection_as_capped_command_basics(database_client, collection, test):
    """Test cloneCollectionAsCapped command basic behavior."""
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
