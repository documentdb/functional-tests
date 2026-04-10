"""
Smoke test for $pull update operator.

Tests basic $pull functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_pull(collection):
    """Test basic $pull behavior."""
    collection.insert_one({"_id": 1, "items": ["A", "B", "C", "B"]})

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": "B"}}}]},
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $pull operator")
