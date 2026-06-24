"""Tests for setFeatureCompatibilityVersion version field BSON type validation.

Validates that the version field only accepts string type and rejects
all other BSON types with TYPE_MISMATCH_ERROR (14).
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command

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


VERSION_TYPE_PARAM = [
    BsonTypeTestCase(
        id="version_value",
        msg="setFeatureCompatibilityVersion should only accept string for version",
        keyword="setFeatureCompatibilityVersion",
        valid_types=[BsonType.STRING],
        skip_rejection_types=[BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
        requires={"confirm": True},
    ),
]

VERSION_TYPE_REJECTIONS = generate_bson_rejection_test_cases(VERSION_TYPE_PARAM)


@pytest.mark.parametrize("bson_type,sample_value,spec", VERSION_TYPE_REJECTIONS)
def test_setFeatureCompatibilityVersion_version_type_rejected(
    collection, bson_type, sample_value, spec
):
    """Test version field rejects non-string BSON types with TYPE_MISMATCH_ERROR."""
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": sample_value, "confirm": True},
    )
    assertFailureCode(
        result,
        spec.expected_code(bson_type),
        msg=f"setFeatureCompatibilityVersion should reject {bson_type.value} for version",
    )


def test_setFeatureCompatibilityVersion_version_string_accepted(collection):
    """Test version field accepts string type (the current version)."""
    current_fcv = _get_fcv(collection)
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": current_fcv, "confirm": True},
    )
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="setFeatureCompatibilityVersion should accept string version"
    )


def test_setFeatureCompatibilityVersion_version_null_rejected(collection):
    """Test version field with null value is rejected (treated as missing field)."""
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": None, "confirm": True},
    )
    # null for version is treated as missing required field (code 40414)
    assertFailureCode(
        result, 40414, msg="setFeatureCompatibilityVersion should reject null for version"
    )
