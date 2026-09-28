"""Tests for compactStructuredEncryptionData on Queryable Encryption collections.

Verifies the success path, missing-token rejection, and token content validation
on collections that are actually configured for Queryable Encryption. These tests
require a replica set (QE collection creation fails on standalone with 6346402).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from bson import Binary

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import MISSING_COMPACT_TOKEN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.requires(queryable_encryption=True)


@pytest.fixture()
def qe_collection(collection):
    """Create a Queryable Encryption collection with one encrypted field."""
    db = collection.database
    qe_name = f"{collection.name}_qe"
    db.command(
        "create",
        qe_name,
        encryptedFields={
            "fields": [
                {
                    "path": "ssn",
                    "bsonType": "string",
                    "keyId": Binary(uuid4().bytes, 4),
                }
            ]
        },
    )
    yield db[qe_name]
    db.drop_collection(qe_name)


# Property [Success Path]: compactStructuredEncryptionData succeeds on a QE collection
# with a valid compaction token and returns stats.
SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "valid_token",
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {"ssn": Binary(b"\x00" * 32, 0)},
        },
        expected={"ok": 1.0},
        msg="compactStructuredEncryptionData should succeed with valid token on QE collection.",
    ),
    CommandTestCase(
        "null_token_value",
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {"ssn": None},
        },
        expected={"ok": 1.0},
        msg="compactStructuredEncryptionData should accept null token value on QE collection.",
    ),
    CommandTestCase(
        "nested_document_token_value",
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {"ssn": {"nested": b"\x00\x01"}},
        },
        expected={"ok": 1.0},
        msg="compactStructuredEncryptionData should accept nested document token value"
        " on QE collection.",
    ),
]

# Property [Token Rejection]: compactStructuredEncryptionData rejects tokens that do not
# match an encrypted path on a QE collection.
ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "missing_token_empty_tokens",
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {},
        },
        error_code=MISSING_COMPACT_TOKEN_ERROR,
        msg="compactStructuredEncryptionData should reject empty compactionTokens"
        " on QE collection.",
    ),
    CommandTestCase(
        "empty_string_key",
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {"": Binary(b"\x00" * 32, 0)},
        },
        error_code=MISSING_COMPACT_TOKEN_ERROR,
        msg="compactStructuredEncryptionData should reject empty-string token key"
        " that does not match an encrypted path.",
    ),
    CommandTestCase(
        "dot_notation_key",
        command=lambda ctx: {
            "compactStructuredEncryptionData": ctx.collection,
            "compactionTokens": {"a.b": Binary(b"\x00" * 32, 0)},
        },
        error_code=MISSING_COMPACT_TOKEN_ERROR,
        msg="compactStructuredEncryptionData should reject dot-notation token key"
        " that does not match an encrypted path.",
    ),
]

QE_SUCCESS_TESTS: list[CommandTestCase] = SUCCESS_TESTS
QE_ERROR_TESTS: list[CommandTestCase] = ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(QE_SUCCESS_TESTS))
def test_compactStructuredEncryptionData_qe_success(qe_collection, test):
    """Test compactStructuredEncryptionData succeeds on QE collection."""
    ctx = CommandContext.from_collection(qe_collection)
    result = execute_command(qe_collection, test.build_command(ctx))
    assertSuccessPartial(result, test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(QE_ERROR_TESTS))
def test_compactStructuredEncryptionData_qe_error(qe_collection, test):
    """Test compactStructuredEncryptionData rejects invalid tokens on QE collection."""
    ctx = CommandContext.from_collection(qe_collection)
    result = execute_command(qe_collection, test.build_command(ctx))
    assertFailureCode(result, test.error_code, msg=test.msg)
