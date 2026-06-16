"""
Smoke test for $[] positional-all update operator.

Tests basic $[] positional-all functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_positional_all(collection):
    """Test basic $[] positional-all behavior."""
    collection.insert_one({"_id": 1, "items": [{"value": 10}, {"value": 20}]})

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"items.$[].value": 0}}}],
        },
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $[] positional-all operator")
