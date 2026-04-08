"""
Smoke test for $pullAll update operator.

Tests basic $pullAll functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_pullAll(collection):
    """Test basic $pullAll behavior."""
    collection.insert_one({"_id": 1, "items": ["A", "B", "C", "D"]})

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pullAll": {"items": ["B", "D"]}}}],
        },
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $pullAll operator")
