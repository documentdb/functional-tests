"""
Smoke test for $switch expression.

Tests basic $switch expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_switch(collection):
    """Test basic $switch expression behavior."""
    collection.insert_many(
        [{"_id": 1, "grade": "A"}, {"_id": 2, "grade": "B"}, {"_id": 3, "grade": "C"}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "score": {
                            "$switch": {
                                "branches": [
                                    {"case": {"$eq": ["$grade", "A"]}, "then": 90},
                                    {"case": {"$eq": ["$grade", "B"]}, "then": 80},
                                ],
                                "default": 70,
                            }
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "score": 90}, {"_id": 2, "score": 80}, {"_id": 3, "score": 70}]
    assertSuccess(result, expected, msg="Should support $switch expression")
