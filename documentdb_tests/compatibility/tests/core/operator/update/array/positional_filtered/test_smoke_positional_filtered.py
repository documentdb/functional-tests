"""
Smoke test for $[<identifier>] positional-filtered update operator.

Tests basic $[<identifier>] positional-filtered functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_positional_filtered(collection):
    """Test basic $[<identifier>] positional-filtered behavior."""
    collection.insert_one({"_id": 1, "items": [{"value": 10}, {"value": 20}, {"value": 30}]})

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"items.$[elem].value": 0}},
                    "arrayFilters": [{"elem.value": {"$gte": 20}}],
                }
            ],
        },
    )

    expected = {"n": 1, "nModified": 1, "ok": 1.0}
    assertSuccessPartial(
        result, expected, msg="Should support $[<identifier>] positional-filtered operator"
    )
