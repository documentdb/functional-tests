"""
Smoke test for $toHashedIndexKey expression.

Tests basic $toHashedIndexKey expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_toHashedIndexKey(collection):
    """Test basic $toHashedIndexKey expression behavior."""
    collection.insert_many([{"_id": 1, "userId": "user123"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"hashedKey": {"$toHashedIndexKey": "$userId"}}}],
            "cursor": {},
        },
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $toHashedIndexKey expression")
