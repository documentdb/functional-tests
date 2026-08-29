"""
Smoke test for ttl index property.

Tests basic TTL index functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexes_ttl(collection):
    """Test basic ttl index behavior."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"createdAt": 1}, "name": "createdAt_ttl", "expireAfterSeconds": 3600.0}
            ],
        },
    )

    assertCommandSupported(result, msg="Should support ttl index property")
