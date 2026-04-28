"""
Smoke test for $sum window operator.

Tests basic $sum window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_sum(collection):
    """Test basic $sum window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "partition": "A", "value": 10},
            {"_id": 2, "partition": "A", "value": 20},
            {"_id": 3, "partition": "A", "value": 30},
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
                            "runningSum": {
                                "$sum": "$value",
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
        {"_id": 1, "partition": "A", "value": 10, "runningSum": 10},
        {"_id": 2, "partition": "A", "value": 20, "runningSum": 30},
        {"_id": 3, "partition": "A", "value": 30, "runningSum": 60},
    ]
    assertSuccess(result, expected, msg="Should support $sum window operator")
