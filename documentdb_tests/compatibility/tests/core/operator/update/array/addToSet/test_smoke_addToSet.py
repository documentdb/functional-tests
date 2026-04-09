"""
Smoke test for $addToSet update operator.

Tests basic $addToSet functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_addToSet(collection):
    """Test basic $addToSet behavior."""
    collection.insert_one({"_id": 1, "tags": ["A", "B"]})

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"tags": "C"}}}],
        },
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $addToSet operator")
