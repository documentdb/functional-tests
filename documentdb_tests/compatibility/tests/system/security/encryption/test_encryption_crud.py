"""Tests for CRUD operations against Queryable Encryption collections.

Verifies insert, update, and delete operations with encryption feature. Any
plaintext value at an encrypted path is rejected, including null and regardless
of bsonType. Absent fields are unaffected.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import DOCUMENT_VALIDATION_FAILURE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.requires(queryable_encryption=True)


# Property [Missing Field Acceptance]: insert succeeds when an encrypted field is absent.
@pytest.mark.insert
def test_encryption_insert_missing_field_succeeds(qe_collection):
    """Test insert succeeds when the encrypted field is entirely absent."""
    result = execute_command(
        qe_collection, {"insert": qe_collection.name, "documents": [{"_id": 1}]}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "n": 1},
        msg="insert should accept a document missing the encrypted field.",
    )


# Property [Plaintext Rejection]: insert rejects null and any plaintext value at an
# encrypted path, regardless of bsonType.
INSERT_PLAINTEXT_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_value",
        command=lambda ctx: {"insert": ctx.collection, "documents": [{"_id": 1, "ssn": None}]},
        error_code=DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="insert should reject an explicit null at an encrypted path.",
    ),
    CommandTestCase(
        "plaintext_matching_bsontype",
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 2, "ssn": "123-45-6789"}],
        },
        error_code=DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="insert should reject a plaintext value even when it matches the declared bsonType.",
    ),
    CommandTestCase(
        "plaintext_wrong_bsontype",
        command=lambda ctx: {"insert": ctx.collection, "documents": [{"_id": 3, "ssn": 123}]},
        error_code=DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="insert should reject a plaintext value of the wrong bsonType.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(INSERT_PLAINTEXT_REJECTION_TESTS))
def test_encryption_insert_rejects_plaintext(qe_collection, test: CommandTestCase):
    """Test insert rejects plaintext values at an encrypted path."""
    ctx = CommandContext.from_collection(qe_collection)
    result = execute_command(qe_collection, test.build_command(ctx))
    assertFailureCode(result, test.error_code, msg=test.msg)


# Property [Multi-Field Independence]: each declared encrypted field is validated
# independently of the others.
@pytest.mark.insert
def test_encryption_insert_multiple_fields_all_absent(qe_collection_multi):
    """Test insert succeeds when every declared encrypted field is absent."""
    result = execute_command(
        qe_collection_multi,
        {"insert": qe_collection_multi.name, "documents": [{"_id": 1, "name": "a"}]},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "n": 1},
        msg="insert should accept a document missing every encrypted field.",
    )


@pytest.mark.insert
def test_encryption_insert_one_of_multiple_fields_plaintext_rejected(qe_collection_multi):
    """Test insert rejects a plaintext value on one of several encrypted fields."""
    result = execute_command(
        qe_collection_multi,
        {"insert": qe_collection_multi.name, "documents": [{"_id": 1, "dob": "2000-01-01"}]},
    )
    assertFailureCode(
        result,
        DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="insert should reject a plaintext value on any one of several encrypted fields.",
    )


# Property [Update Enforcement]: update applies the same validation as insert.
@pytest.mark.update
def test_encryption_update_rejects_plaintext(qe_collection):
    """Test update rejects setting an encrypted field to a plaintext value."""
    qe_collection.insert_one({"_id": 1})
    result = execute_command(
        qe_collection,
        {
            "update": qe_collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"ssn": "123-45-6789"}}}],
        },
    )
    assertFailureCode(
        result,
        DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="update should reject a plaintext value written to an encrypted path.",
    )


# Property [Delete Unaffected]: delete is unaffected by the collection's encryption schema.
@pytest.mark.delete
def test_encryption_delete_succeeds(qe_collection):
    """Test delete succeeds for a document with an absent encrypted field."""
    qe_collection.insert_one({"_id": 1})
    result = execute_command(
        qe_collection, {"delete": qe_collection.name, "deletes": [{"q": {"_id": 1}, "limit": 1}]}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "n": 1},
        msg="delete should succeed on a Queryable Encryption collection.",
    )
