"""Tests for startSession stable API acceptance."""

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

# Property [Stable API Acceptance]: startSession is accepted with apiVersion 1
# when apiStrict is not true.
STARTSESSION_STABLE_API_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "stable_api_version_1_alone",
        command=lambda ctx: {"startSession": 1, "apiVersion": "1"},
        expected={"ok": Eq(1.0)},
        msg="startSession should succeed with apiVersion 1 alone",
    ),
    CommandTestCase(
        "stable_api_version_1_strict_false",
        command=lambda ctx: {"startSession": 1, "apiVersion": "1", "apiStrict": False},
        expected={"ok": Eq(1.0)},
        msg="startSession should succeed with apiVersion 1 and apiStrict false",
    ),
    CommandTestCase(
        "stable_api_version_1_deprecation_true",
        command=lambda ctx: {
            "startSession": 1,
            "apiVersion": "1",
            "apiDeprecationErrors": True,
        },
        expected={"ok": Eq(1.0)},
        msg="startSession should succeed with apiVersion 1 and apiDeprecationErrors true",
    ),
    CommandTestCase(
        "stable_api_version_1_deprecation_false",
        command=lambda ctx: {
            "startSession": 1,
            "apiVersion": "1",
            "apiDeprecationErrors": False,
        },
        expected={"ok": Eq(1.0)},
        msg="startSession should succeed with apiVersion 1 and apiDeprecationErrors false",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_STABLE_API_ACCEPTANCE_TESTS))
def test_startSession_stable_api_acceptance(database_client, collection, test):
    """Test startSession stable API acceptance."""
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
