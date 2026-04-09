"""
Smoke test for $topN window operator.

Tests basic $topN window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_topN(collection):
    """Test basic $topN window operator behavior."""
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
                            "topScores": {
                                "$topN": {
                                    "sortBy": {"score": -1},
                                    "output": "$name",
                                    "n": 2,
                                },
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
        {"_id": 1, "partition": "A", "score": 90, "name": "Alice", "topScores": ["Alice"]},
        {
            "_id": 2,
            "partition": "A",
            "score": 100,
            "name": "Bob",
            "topScores": ["Bob", "Alice"],
        },
        {
            "_id": 3,
            "partition": "A",
            "score": 85,
            "name": "Charlie",
            "topScores": ["Bob", "Alice"],
        },
    ]
    assertSuccess(result, expected, msg="Should support $topN window operator")
