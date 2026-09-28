"""Smoke test for compactStructuredEncryptionData command.

Tests basic compactStructuredEncryptionData functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import NOT_ENCRYPTED_COLLECTION_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_compactStructuredEncryptionData(collection):
    """Test basic compactStructuredEncryptionData behavior."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection, {"compactStructuredEncryptionData": collection.name, "compactionTokens": {}}
    )

    assertFailureCode(
        result,
        NOT_ENCRYPTED_COLLECTION_ERROR,
        msg="compactStructuredEncryptionData should reject non-encrypted collection",
    )
