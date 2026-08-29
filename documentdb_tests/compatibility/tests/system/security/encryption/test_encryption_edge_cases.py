"""Tests for encryption edge cases: nested paths, value size, and multiplicity.

Verifies that no value shape other than absence can be written to an encrypted
path without a client FLE driver, regardless of nesting, size, or document
count.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import DOCUMENT_VALIDATION_FAILURE_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.requires(queryable_encryption=True)


# Property [Nested Path Independence]: a nested encrypted path is unaffected by
# insert as long as it is absent, regardless of whether its parent object is present.
@pytest.mark.insert
def test_encryption_insert_nested_path_missing_parent_succeeds(qe_collection_nested):
    """Test insert succeeds when the parent of a nested encrypted path is absent."""
    result = execute_command(
        qe_collection_nested, {"insert": qe_collection_nested.name, "documents": [{"_id": 1}]}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "n": 1},
        msg="insert should succeed when the parent object of a nested encrypted path is absent.",
    )


@pytest.mark.insert
def test_encryption_insert_nested_path_parent_present_child_absent_succeeds(qe_collection_nested):
    """Test insert succeeds when the parent object is present but the encrypted child is absent."""
    result = execute_command(
        qe_collection_nested,
        {"insert": qe_collection_nested.name, "documents": [{"_id": 1, "address": {"city": "x"}}]},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "n": 1},
        msg="insert should succeed when a nested encrypted field is absent"
        " even if its parent object is present.",
    )


@pytest.mark.insert
def test_encryption_insert_nested_path_plaintext_rejected(qe_collection_nested):
    """Test insert rejects a plaintext value at a nested encrypted path."""
    result = execute_command(
        qe_collection_nested,
        {
            "insert": qe_collection_nested.name,
            "documents": [{"_id": 1, "address": {"ssn": "123-45-6789"}}],
        },
    )
    assertFailureCode(
        result,
        DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="insert should reject a plaintext value at a nested encrypted path.",
    )


# Property [Validation Ignores Size]: a plaintext value at an encrypted path is
# rejected regardless of its size.
@pytest.mark.insert
def test_encryption_insert_large_plaintext_value_rejected(qe_collection):
    """Test insert rejects a large plaintext value at an encrypted path."""
    result = execute_command(
        qe_collection,
        {"insert": qe_collection.name, "documents": [{"_id": 1, "ssn": "x" * 4_000}]},
    )
    assertFailureCode(
        result,
        DOCUMENT_VALIDATION_FAILURE_ERROR,
        msg="insert should reject an oversized plaintext value at an encrypted path"
        " just as it would a small one.",
    )


# Property [Absence Has No Multiplicity Constraint]: several documents may each omit
# the same encrypted field in one insert; equality does not impose uniqueness on absence.
@pytest.mark.insert
def test_encryption_insert_multiple_documents_all_missing_field(qe_collection):
    """Test a batch insert succeeds when every document omits the same encrypted field."""
    result = execute_command(
        qe_collection,
        {"insert": qe_collection.name, "documents": [{"_id": 1}, {"_id": 2}]},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "n": 2},
        msg="a batch insert should succeed when every document omits the same encrypted field.",
    )


# Property [Explain Compatibility]: explain runs normally against a
# Queryable Encryption collection.
@pytest.mark.find
def test_encryption_explain_find_on_encrypted_collection(qe_collection):
    """Test explain succeeds for a find against a Queryable Encryption collection."""
    result = execute_command(
        qe_collection,
        {"explain": {"find": qe_collection.name, "filter": {"ssn": "x"}}},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="explain should succeed for a find against a Queryable Encryption collection.",
    )
