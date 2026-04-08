"""
Smoke test for $unset update operator.

Tests basic $unset functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_update_unset(collection):
    """Test basic $unset behavior."""
    collection.insert_one({"_id": 1, "name": "test", "extra": "remove"})

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$unset": {"extra": ""}}}]},
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $unset operator")
