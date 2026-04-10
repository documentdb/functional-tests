"""
Smoke test for $ positional update operator.

Tests basic $ positional functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_update_positional(collection):
    """Test basic $ positional behavior."""
    collection.insert_one(
        {"_id": 1, "items": [{"name": "A", "value": 10}, {"name": "B", "value": 20}]}
    )

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1, "items.name": "A"}, "u": {"$set": {"items.$.value": 15}}}],
        },
    )
    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $ positional operator")
