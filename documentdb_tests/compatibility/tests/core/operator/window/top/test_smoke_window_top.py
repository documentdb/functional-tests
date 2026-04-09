"""
Smoke test for $top window operator.

Tests basic $top window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_top(collection):
    """Test basic $top window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "partition": "A", "score": 90, "name": "Alice"},
            {"_id": 2, "partition": "A", "score": 100, "name": "Bob"},
            {"_id": 3, "partition": "A", "score": 85, "name": "Charlie"},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "topScore": {
                                "$top": {"sortBy": {"score": -1}, "output": "$name"},
                                "window": {"documents": ["unbounded", "current"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "partition": "A", "score": 90, "name": "Alice", "topScore": "Alice"},
        {"_id": 2, "partition": "A", "score": 100, "name": "Bob", "topScore": "Bob"},
        {"_id": 3, "partition": "A", "score": 85, "name": "Charlie", "topScore": "Bob"},
    ]
    assertSuccess(result, expected, msg="Should support $top window operator")
