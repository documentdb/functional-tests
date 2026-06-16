"""Tests for startSession readConcern acceptance."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [readConcern Document Acceptance]: valid document readConcern values are accepted.
STARTSESSION_RC_DOC_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_doc_accept_empty",
        command=lambda ctx: {"startSession": 1, "readConcern": {}},
        expected={"ok": Eq(1.0)},
        msg="startSession should accept empty document readConcern",
    ),
    CommandTestCase(
        "rc_doc_accept_null",
        command=lambda ctx: {"startSession": 1, "readConcern": None},
        expected={"ok": Eq(1.0)},
        msg="startSession should accept null readConcern as omitted",
    ),
    CommandTestCase(
        "rc_doc_accept_level_local",
        command=lambda ctx: {"startSession": 1, "readConcern": {"level": "local"}},
        expected={"ok": Eq(1.0)},
        msg="startSession should accept readConcern level local",
    ),
    CommandTestCase(
        "rc_doc_accept_level_null",
        command=lambda ctx: {"startSession": 1, "readConcern": {"level": None}},
        expected={"ok": Eq(1.0)},
        msg="startSession should accept readConcern with null level",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_RC_DOC_ACCEPTANCE_TESTS))
def test_startSession_readconcern_acceptance(database_client, collection, test):
    """Test startSession readConcern acceptance."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=True,
    )
    if isinstance(result, dict) and "id" in result:
        collection.database.command({"endSessions": [result["id"]]})
