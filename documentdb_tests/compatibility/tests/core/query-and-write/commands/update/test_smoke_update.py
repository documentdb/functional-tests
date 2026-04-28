"""
Smoke test for update command.

Tests basic update command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_update(collection):
    """Test basic update command behavior."""
    collection.insert_one({"_id": 1, "name": "Alice", "count": 10})

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"name": "Bob"}}}],
        },
    )

    expected = {"ok": 1.0, "n": 1, "nModified": 1}
    assertSuccessPartial(result, expected, msg="Should support update command")
