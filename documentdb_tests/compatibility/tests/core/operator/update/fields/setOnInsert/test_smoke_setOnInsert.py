"""
Smoke test for $setOnInsert update operator.

Tests basic $setOnInsert functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_setOnInsert(collection):
    """Test basic $setOnInsert behavior."""
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$setOnInsert": {"created": True}}, "upsert": True}
            ],
        },
    )
    expected = {"n": 1, "nModified": 0, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $setOnInsert operator")
