"""
Smoke test for $min update operator.

Tests basic $min functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_min(collection):
    """Test basic $min behavior."""
    collection.insert_one({"_id": 1, "score": 10})

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$min": {"score": 5}}}]},
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $min operator")
