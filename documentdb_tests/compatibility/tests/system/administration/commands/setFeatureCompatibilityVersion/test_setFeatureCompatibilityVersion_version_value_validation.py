"""Tests for setFeatureCompatibilityVersion version value validation.

Validates that the version field rejects unsupported, malformed, and
edge-case string values.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import FCV_INVALID_VERSION_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def _get_fcv(collection):
    """Read the current FCV via getParameter."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    if isinstance(result, Exception):
        return "8.2"
    fcv_data = result.get("featureCompatibilityVersion", {})
    if isinstance(fcv_data, dict):
        return fcv_data.get("version", "8.2")
    return str(fcv_data)


# Property [Invalid Version Rejected]: setFeatureCompatibilityVersion rejects
# unsupported, malformed, and edge-case version strings.
VERSION_VALUE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "below_floor",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "3.0", "confirm": True},
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject version below supported floor",
    ),
    CommandTestCase(
        "above_max",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "99.0", "confirm": True},
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject version above supported max",
    ),
    CommandTestCase(
        "major_only",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "8", "confirm": True},
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject major-only version string",
    ),
    CommandTestCase(
        "full_semver",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "8.0.0", "confirm": True},
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject full semver version string",
    ),
    CommandTestCase(
        "leading_whitespace",
        command=lambda ctx: {"setFeatureCompatibilityVersion": " 7.0", "confirm": True},
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject version with leading whitespace",
    ),
    CommandTestCase(
        "trailing_whitespace",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "7.0 ", "confirm": True},
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject version with trailing whitespace",
    ),
    CommandTestCase(
        "empty_string",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "", "confirm": True},
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject empty string version",
    ),
    CommandTestCase(
        "zero_version",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "0.0", "confirm": True},
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject '0.0' as unsupported",
    ),
    CommandTestCase(
        "future_version",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "10.0", "confirm": True},
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject future unsupported version",
    ),
    CommandTestCase(
        "non_ascii",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "\uff18.\uff10",
            "confirm": True,
        },
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject non-ASCII version string",
    ),
    CommandTestCase(
        "very_long_string",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "8" * 10_000,
            "confirm": True,
        },
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject a very long version string",
    ),
    CommandTestCase(
        "intermediate_value",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "7.5", "confirm": True},
        error_code=FCV_INVALID_VERSION_ERROR,
        msg="setFeatureCompatibilityVersion should reject intermediate version value",
    ),
]


# Property [Current Version Accepted]: setFeatureCompatibilityVersion accepts
# the current binary version.
CURRENT_VERSION_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "current_version",
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept the current binary version",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VERSION_VALUE_REJECTION_TESTS))
def test_setFeatureCompatibilityVersion_version_value_rejected(database_client, collection, test):
    """Test setFeatureCompatibilityVersion rejects invalid version values."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(CURRENT_VERSION_ACCEPTED_TESTS))
def test_setFeatureCompatibilityVersion_current_version_accepted(database_client, collection, test):
    """Test setFeatureCompatibilityVersion accepts the current binary version."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": fcv, "confirm": True}
    )
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
