"""Tests for compactStructuredEncryptionData on Queryable Encryption collections.

Verifies the success path and missing-token rejection on collections that
are actually configured for Queryable Encryption. These tests require a
replica set (QE collection creation fails on standalone with 6346402).
"""

from uuid import uuid4

import pytest
from bson import Binary

from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.error_codes import MISSING_COMPACT_TOKEN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Exists

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
# with a valid compaction token and returns stats with esc and ecoc sub-documents.
def test_compact_success_returns_stats(qe_collection):
    """Test compactStructuredEncryptionData succeeds on a QE collection with valid token."""
    token = Binary(b"\x00" * 32, 0)
    result = execute_command(
        qe_collection,
        {
            "compactStructuredEncryptionData": qe_collection.name,
            "compactionTokens": {"ssn": token},
        },
    )
    assertProperties(
        result,
        {
            "ok": Eq(1.0),
            "stats": Exists(),
            "stats.esc": Exists(),
            "stats.ecoc": Exists(),
        },
        raw_res=True,
        msg="compactStructuredEncryptionData should succeed and return stats on QE collection.",
    )


# Property [Missing Token Rejection]: compactStructuredEncryptionData rejects empty
# compactionTokens on a QE collection when an encrypted path exists.
def test_compact_missing_token_for_encrypted_path(qe_collection):
    """Test compactStructuredEncryptionData rejects empty tokens on QE collection."""
    result = execute_command(
        qe_collection,
        {
            "compactStructuredEncryptionData": qe_collection.name,
            "compactionTokens": {},
        },
    )
    assertFailureCode(
        result,
        MISSING_COMPACT_TOKEN_ERROR,
        msg="compactStructuredEncryptionData should reject missing token for encrypted path.",
    )
