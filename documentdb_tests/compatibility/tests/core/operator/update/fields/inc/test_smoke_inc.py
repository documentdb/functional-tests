"""
Smoke test for $inc update operator.

Tests basic $inc functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_inc(collection):
    """Test basic $inc behavior."""
    collection.insert_one({"_id": 1, "count": 10})

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$inc": {"count": 5}}}]},
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $inc operator")
