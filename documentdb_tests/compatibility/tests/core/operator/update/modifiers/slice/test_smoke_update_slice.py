"""
Smoke test for $slice modifier update operator.

Tests basic $slice modifier functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_update_slice(collection):
    """Test basic $slice modifier behavior."""
    collection.insert_one({"_id": 1, "items": ["A", "B"]})

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$push": {"items": {"$each": ["C", "D"], "$slice": 3}}}}
            ],
        },
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $slice modifier operator")
