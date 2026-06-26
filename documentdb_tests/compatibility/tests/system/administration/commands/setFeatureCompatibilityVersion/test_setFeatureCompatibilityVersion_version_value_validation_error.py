"""Tests for setFeatureCompatibilityVersion version value validation (error cases).

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
