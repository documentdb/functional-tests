"""
Smoke test for findAndModify command.

Tests basic findAndModify command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_findAndModify(collection):
    """Test basic findAndModify command behavior."""
    collection.insert_one({"_id": 1, "name": "Alice", "count": 10})

    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$inc": {"count": 5}},
            "new": True,
        },
    )

    expected = {"ok": 1.0, "value": {"_id": 1, "name": "Alice", "count": 15}}
    assertSuccessPartial(result, expected, msg="Should support findAndModify command")
