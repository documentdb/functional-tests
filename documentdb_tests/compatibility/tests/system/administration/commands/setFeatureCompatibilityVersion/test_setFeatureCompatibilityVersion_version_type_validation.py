"""Tests for setFeatureCompatibilityVersion version field BSON type validation.

Validates that the version field only accepts string type and rejects
all other BSON types with TYPE_MISMATCH_ERROR.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import MISSING_FIELD_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

from .utils.setFeatureCompatibilityVersion_common import get_fcv

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


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
    """Test setFeatureCompatibilityVersion rejects non-string BSON types for version."""
    result = execute_admin_command(
        collection,
        {"setFeatureCompatibilityVersion": sample_value, "confirm": True},
    )
    assertResult(
        result,
        error_code=spec.expected_code(bson_type),
        msg=f"setFeatureCompatibilityVersion should reject {bson_type.value} for version",
        raw_res=True,
    )


# Property [String Accepted]: setFeatureCompatibilityVersion accepts string type.
VERSION_STRING_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "version_string_accepted",
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept string for version",
    ),
]

# Property [Null Rejected]: setFeatureCompatibilityVersion rejects null for version.
VERSION_NULL_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "version_null_rejected",
        command=lambda ctx: {"setFeatureCompatibilityVersion": None, "confirm": True},
        error_code=MISSING_FIELD_ERROR,
        msg="setFeatureCompatibilityVersion should reject null for version",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VERSION_STRING_ACCEPTED_TESTS))
def test_setFeatureCompatibilityVersion_version_string_accepted(database_client, collection, test):
    """Test setFeatureCompatibilityVersion accepts string type for version."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    fcv = get_fcv(collection)
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


@pytest.mark.parametrize("test", pytest_params(VERSION_NULL_REJECTED_TESTS))
def test_setFeatureCompatibilityVersion_version_null_rejected(database_client, collection, test):
    """Test setFeatureCompatibilityVersion rejects null for version."""
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
