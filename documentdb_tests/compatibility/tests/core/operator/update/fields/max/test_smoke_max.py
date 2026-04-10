"""
Smoke test for $max update operator.

Tests basic $max functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_max(collection):
    """Test basic $max behavior."""
    collection.insert_one({"_id": 1, "score": 10})

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"score": 20}}}]},
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $max operator")
