"""
Smoke test for $each modifier update operator.

Tests basic $each modifier functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_each(collection):
    """Test basic $each modifier behavior."""
    collection.insert_one({"_id": 1, "items": ["A"]})

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"items": {"$each": ["B", "C"]}}}}],
        },
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $each modifier operator")
