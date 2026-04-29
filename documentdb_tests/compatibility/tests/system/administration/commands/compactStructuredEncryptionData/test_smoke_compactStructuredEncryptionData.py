"""
Smoke test for compactStructuredEncryptionData command.

Tests basic compactStructuredEncryptionData functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailure
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_compactStructuredEncryptionData(collection):
    """Test basic compactStructuredEncryptionData behavior."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection, {"compactStructuredEncryptionData": collection.name, "compactionTokens": {}}
    )

    expected = {"code": 6346807, "msg": "Target namespace is not an encrypted collection"}
    assertFailure(result, expected, msg="Should support compactStructuredEncryptionData command")
