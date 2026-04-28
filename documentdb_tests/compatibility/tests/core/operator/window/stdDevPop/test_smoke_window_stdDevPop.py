"""
Smoke test for $stdDevPop window operator.

Tests basic $stdDevPop window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_stdDevPop(collection):
    """Test basic $stdDevPop window operator behavior."""
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
                            "stdDev": {
                                "$stdDevPop": "$value",
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
        {"_id": 1, "partition": "A", "value": 10, "stdDev": 0.0},
        {"_id": 2, "partition": "A", "value": 20, "stdDev": 5.0},
        {"_id": 3, "partition": "A", "value": 30, "stdDev": 8.16496580927726},
    ]
    assertSuccess(result, expected, msg="Should support $stdDevPop window operator")
