"""
Smoke test for $currentDate update operator.

Tests basic $currentDate functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_currentDate(collection):
    """Test basic $currentDate behavior."""
    collection.insert_one({"_id": 1, "name": "test"})

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"lastModified": True}}}],
        },
    )

    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $currentDate operator")
