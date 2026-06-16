"""Tests for the create command unrecognized top-level field behavior."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNRECOGNIZED_COMMAND_FIELD_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Unrecognized Top-Level Fields]: unknown fields at the top level of
# the create command produce UNRECOGNIZED_COMMAND_FIELD_ERROR.
CREATE_UNKNOWN_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="unrecognized_top_level_field_rejected",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "completelyBogusField": 42,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized top-level fields should be rejected",
    ),
    CommandTestCase(
        id="unrecognized_top_level_field_with_valid_options",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "unknownExtra": "hello",
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized field alongside valid options should be rejected",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_UNKNOWN_FIELD_TESTS))
def test_create_unknown_fields(database_client, collection, test):
    """Test create command unrecognized top-level field behavior."""
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
