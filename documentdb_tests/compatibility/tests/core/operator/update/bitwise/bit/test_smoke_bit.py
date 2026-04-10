"""
Smoke test for $bit update operator.

Tests basic $bit functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_bit(collection):
    """Test basic $bit behavior."""
    collection.insert_one({"_id": 1, "value": 5})

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$bit": {"value": {"and": 3}}}}],
        },
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $bit operator")
