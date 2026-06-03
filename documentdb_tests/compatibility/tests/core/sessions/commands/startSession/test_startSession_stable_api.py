"""Tests for startSession stable API behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    API_STRICT_ERROR,
    API_VERSION_ERROR,
    API_VERSION_REQUIRED_ERROR,
)
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

# Property [Stable API Rejection]: startSession is NOT in API Version 1
# and is rejected with apiStrict true.
STARTSESSION_STABLE_API_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "stable_api_strict_true_rejected",
        command=lambda ctx: {"startSession": 1, "apiVersion": "1", "apiStrict": True},
        error_code=API_STRICT_ERROR,
        msg="startSession should be rejected with apiVersion 1 and apiStrict true",
    ),
    CommandTestCase(
        "stable_api_invalid_version",
        command=lambda ctx: {"startSession": 1, "apiVersion": "2"},
        error_code=API_VERSION_ERROR,
        msg="startSession should reject invalid apiVersion 2",
    ),
    CommandTestCase(
        "stable_api_empty_version",
        command=lambda ctx: {"startSession": 1, "apiVersion": ""},
        error_code=API_VERSION_ERROR,
        msg="startSession should reject empty string apiVersion",
    ),
    CommandTestCase(
        "stable_api_strict_without_version",
        command=lambda ctx: {"startSession": 1, "apiStrict": True},
        error_code=API_VERSION_REQUIRED_ERROR,
        msg="startSession should reject apiStrict without apiVersion",
    ),
    CommandTestCase(
        "stable_api_deprecation_without_version",
        command=lambda ctx: {"startSession": 1, "apiDeprecationErrors": True},
        error_code=API_VERSION_REQUIRED_ERROR,
        msg="startSession should reject apiDeprecationErrors without apiVersion",
    ),
]

STARTSESSION_STABLE_API_SUCCESS_TESTS = STARTSESSION_STABLE_API_ACCEPTANCE_TESTS

STARTSESSION_STABLE_API_ERROR_TESTS = STARTSESSION_STABLE_API_REJECTION_TESTS

STARTSESSION_STABLE_API_TESTS = (
    STARTSESSION_STABLE_API_SUCCESS_TESTS + STARTSESSION_STABLE_API_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_STABLE_API_TESTS))
def test_startSession_stable_api(database_client, collection, test):
    """Test startSession stable API acceptance and rejection."""
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
