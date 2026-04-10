"""
Smoke test for $cond expression.

Tests basic $cond expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_cond(collection):
    """Test basic $cond expression behavior."""
    collection.insert_many([{"_id": 1, "qty": 250}, {"_id": 2, "qty": 150}, {"_id": 3, "qty": 300}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "status": {
                            "$cond": {"if": {"$gte": ["$qty", 250]}, "then": "high", "else": "low"}
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "status": "high"},
        {"_id": 2, "status": "low"},
        {"_id": 3, "status": "high"},
    ]
    assertSuccess(result, expected, msg="Should support $cond expression")
