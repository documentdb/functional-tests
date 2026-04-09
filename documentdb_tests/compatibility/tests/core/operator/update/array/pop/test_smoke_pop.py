"""
Smoke test for $pop update operator.

Tests basic $pop functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_pop(collection):
    """Test basic $pop behavior."""
    collection.insert_one({"_id": 1, "items": ["A", "B", "C"]})

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 1}}}]},
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $pop operator")
