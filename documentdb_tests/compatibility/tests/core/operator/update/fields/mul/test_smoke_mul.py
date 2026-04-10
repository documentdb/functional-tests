"""
Smoke test for $mul update operator.

Tests basic $mul functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_mul(collection):
    """Test basic $mul behavior."""
    collection.insert_one({"_id": 1, "value": 10})

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"value": 3}}}]},
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $mul operator")
