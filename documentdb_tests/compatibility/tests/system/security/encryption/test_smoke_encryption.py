"""
Smoke test for encryption.

Tests basic encryption functionality.
"""

from uuid import uuid4

import pytest
from bson.binary import Binary

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_encryption(collection):
    """Test basic encryption behavior."""
    result = execute_command(
        collection,
        {
            "create": "encrypted_collection",
            "encryptedFields": {
                "fields": [{"path": "ssn", "bsonType": "string", "keyId": Binary(uuid4().bytes, 4)}]
            },
        },
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support encryption")
