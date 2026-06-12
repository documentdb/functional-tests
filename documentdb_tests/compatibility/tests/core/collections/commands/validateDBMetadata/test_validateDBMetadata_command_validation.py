"""Tests for validateDBMetadata null/missing and unrecognized field errors."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    MISSING_FIELD_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null and Missing Errors]: null or omitted apiParameters and
# apiParameters.version are treated as missing and rejected.
VALIDATE_DB_METADATA_NULL_MISSING_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_err_api_parameters_null",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": None,
        },
        error_code=MISSING_FIELD_ERROR,
        msg="validateDBMetadata should reject null apiParameters as missing",
    ),
    CommandTestCase(
        "null_err_api_parameters_omitted",
        command=lambda ctx: {
            "validateDBMetadata": 1,
        },
        error_code=MISSING_FIELD_ERROR,
        msg="validateDBMetadata should reject omitted apiParameters",
    ),
    CommandTestCase(
        "null_err_version_null",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": None, "strict": True},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="validateDBMetadata should reject null apiParameters.version as missing",
    ),
    CommandTestCase(
        "null_err_version_omitted",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"strict": True},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="validateDBMetadata should reject omitted apiParameters.version",
    ),
    CommandTestCase(
        "null_err_api_parameters_empty_doc",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="validateDBMetadata should reject empty apiParameters document",
    ),
]

# Property [Unrecognized Field Errors]: unrecognized fields at the top
# level or inside apiParameters are rejected.
VALIDATE_DB_METADATA_UNRECOGNIZED_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unrecognized_top_level_field",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "unknownField": 1,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="validateDBMetadata should reject unrecognized top-level field",
    ),
    CommandTestCase(
        "unrecognized_api_params_field",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True, "unknown": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="validateDBMetadata should reject unrecognized field inside apiParameters",
    ),
    CommandTestCase(
        "unrecognized_case_sensitive_strict",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "Strict": True},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="validateDBMetadata should reject case-mismatched field inside apiParameters",
    ),
    CommandTestCase(
        "unrecognized_dollar_prefix",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "$unknown": 1,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="validateDBMetadata should reject dollar-prefixed unknown top-level field",
    ),
]

VALIDATE_DB_METADATA_COMMAND_VALIDATION_TESTS: list[CommandTestCase] = (
    VALIDATE_DB_METADATA_NULL_MISSING_ERROR_TESTS
    + VALIDATE_DB_METADATA_UNRECOGNIZED_FIELD_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VALIDATE_DB_METADATA_COMMAND_VALIDATION_TESTS))
def test_validateDBMetadata_command_validation(database_client, collection, test):
    """Test validateDBMetadata null/missing and unrecognized field errors."""
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
