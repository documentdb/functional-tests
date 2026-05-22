"""Tests for validateDBMetadata readConcern and writeConcern handling."""

from __future__ import annotations

import pytest
from bson import Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    ILLEGAL_OPERATION_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [readConcern Acceptance (Smoke)]: the command accepts
# level "local" and an omitted or empty readConcern document.
VALIDATE_DB_METADATA_READ_CONCERN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "read_concern_local",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
            "readConcern": {"level": "local"},
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept readConcern level local",
    ),
    CommandTestCase(
        "read_concern_empty_doc",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
            "readConcern": {},
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should accept empty readConcern document",
    ),
]

# Property [readConcern Errors (Smoke)]: unsupported or unrecognized
# readConcern levels and non-document types are rejected.
VALIDATE_DB_METADATA_READ_CONCERN_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "read_concern_err_majority",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "readConcern": {"level": "majority"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="validateDBMetadata should reject readConcern level majority",
    ),
    CommandTestCase(
        "read_concern_err_available",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "readConcern": {"level": "available"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="validateDBMetadata should reject readConcern level available",
    ),
    CommandTestCase(
        "read_concern_err_linearizable",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "readConcern": {"level": "linearizable"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="validateDBMetadata should reject readConcern level linearizable",
    ),
    CommandTestCase(
        "read_concern_err_snapshot",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "readConcern": {"level": "snapshot"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="validateDBMetadata should reject readConcern level snapshot",
    ),
    CommandTestCase(
        "read_concern_err_invalid_level",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "readConcern": {"level": "bogus"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="validateDBMetadata should reject unrecognized readConcern level",
    ),
    CommandTestCase(
        "read_concern_err_non_document",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "readConcern": "local",
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="validateDBMetadata should reject non-document readConcern",
    ),
    CommandTestCase(
        "read_concern_err_unrecognized_field",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "readConcern": {"level": "local", "unknown": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="validateDBMetadata should reject unrecognized field inside readConcern",
    ),
    CommandTestCase(
        "read_concern_err_after_cluster_time_null",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "readConcern": {"level": "local", "afterClusterTime": None},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="validateDBMetadata should reject null afterClusterTime in readConcern",
    ),
    CommandTestCase(
        "read_concern_err_after_cluster_time_valid",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "readConcern": {"level": "local", "afterClusterTime": Timestamp(1, 1)},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="validateDBMetadata should reject afterClusterTime in readConcern",
    ),
]

# Property [writeConcern Errors (Smoke)]: the command does not support
# writeConcern and rejects any writeConcern value.
VALIDATE_DB_METADATA_WRITE_CONCERN_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "write_concern_err_w1",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "writeConcern": {"w": 1},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="validateDBMetadata should reject writeConcern with w:1",
    ),
    CommandTestCase(
        "write_concern_err_w_majority",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "writeConcern": {"w": "majority"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="validateDBMetadata should reject writeConcern with w:majority",
    ),
    CommandTestCase(
        "write_concern_err_empty_doc",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "writeConcern": {},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="validateDBMetadata should reject empty writeConcern document",
    ),
    CommandTestCase(
        "write_concern_err_non_document",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "writeConcern": "majority",
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="validateDBMetadata should reject non-document writeConcern",
    ),
]

VALIDATE_DB_METADATA_READ_WRITE_CONCERN_TESTS: list[CommandTestCase] = (
    VALIDATE_DB_METADATA_READ_CONCERN_ACCEPTANCE_TESTS
    + VALIDATE_DB_METADATA_READ_CONCERN_ERROR_TESTS
    + VALIDATE_DB_METADATA_WRITE_CONCERN_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VALIDATE_DB_METADATA_READ_WRITE_CONCERN_TESTS))
def test_validateDBMetadata_read_write_concern(database_client, collection, test):
    """Test validateDBMetadata readConcern and writeConcern handling."""
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
