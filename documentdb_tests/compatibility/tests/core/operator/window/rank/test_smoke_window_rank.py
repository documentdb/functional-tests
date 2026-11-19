"""
Smoke test for $rank window operator.

Tests basic $rank window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_rank(collection):
    """Test basic $rank window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "partition": "A", "score": 100},
            {"_id": 2, "partition": "A", "score": 100},
            {"_id": 3, "partition": "A", "score": 90},
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
                        "output": {"rank": {"$rank": {}}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $rank window operator")
