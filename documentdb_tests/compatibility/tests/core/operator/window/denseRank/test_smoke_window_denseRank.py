"""
Smoke test for $denseRank window operator.

Tests basic $denseRank window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_denseRank(collection):
    """Test basic $denseRank window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "partition": "A", "score": 100},
            {"_id": 2, "partition": "A", "score": 100},
            {"_id": 3, "partition": "A", "score": 90},
            {"_id": 4, "partition": "B", "score": 80},
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
                        "sortBy": {"score": -1},
                        "output": {"rank": {"$denseRank": {}}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "partition": "A", "score": 100, "rank": 1},
        {"_id": 2, "partition": "A", "score": 100, "rank": 1},
        {"_id": 3, "partition": "A", "score": 90, "rank": 2},
        {"_id": 4, "partition": "B", "score": 80, "rank": 1},
    ]
    assertSuccess(result, expected, msg="Should support $denseRank window operator")
