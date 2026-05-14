"""Tests for compact command unrecognized field handling."""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNRECOGNIZED_COMMAND_FIELD_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Unrecognized Fields Handling]: unrecognized top-level command
# fields are rejected with an unknown field error. Field names are
# case-sensitive.
COMPACT_UNRECOGNIZED_FIELDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "unknownField": "hello"},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized field should be rejected",
    ),
    CommandTestCase(
        "wrong_case_dryrun",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryrun": True},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Wrong-case 'dryrun' should be treated as unknown and rejected",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMPACT_UNRECOGNIZED_FIELDS_TESTS))
def test_compact_unrecognized_fields(database_client, collection, test):
    """Test compact command rejects unrecognized fields."""
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
