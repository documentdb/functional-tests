"""Tests for startSession writeConcern acceptance."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [writeConcern Null Acceptance]: null writeConcern is treated as omitted.
STARTSESSION_WC_NULL_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_null_accepted",
        command=lambda ctx: {"startSession": 1, "writeConcern": None},
        expected={"ok": Eq(1.0)},
        msg="startSession should accept null writeConcern as omitted",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_WC_NULL_ACCEPTANCE_TESTS))
def test_startSession_writeconcern_acceptance(database_client, collection, test):
    """Test startSession writeConcern acceptance."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=True,
    )
