"""
Smoke test for $rename update operator.

Tests basic $rename functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_rename(collection):
    """Test basic $rename behavior."""
    collection.insert_one({"_id": 1, "oldName": "value"})

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$rename": {"oldName": "newName"}}}],
        },
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $rename operator")
