"""
Smoke test for $push update operator.

Tests basic $push functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_push(collection):
    """Test basic $push behavior."""
    collection.insert_one({"_id": 1, "items": ["A", "B"]})

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$push": {"items": "C"}}}]},
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $push operator")
