"""
Smoke test for $toUUID expression.

Tests basic $toUUID expression functionality.
"""

from uuid import UUID

import pytest
from bson.binary import Binary

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_toUUID(collection):
    """Test basic $toUUID expression behavior."""
    collection.insert_many([{"_id": 1, "value": "12345678-1234-1234-1234-123456789012"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"uuid": {"$toUUID": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "uuid": Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789012"))}]
    assertSuccess(result, expected, msg="Should support $toUUID expression")
