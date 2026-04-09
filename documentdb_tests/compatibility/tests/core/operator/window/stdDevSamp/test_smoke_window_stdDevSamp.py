"""
Smoke test for $stdDevSamp window operator.

Tests basic $stdDevSamp window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_stdDevSamp(collection):
    """Test basic $stdDevSamp window operator behavior."""
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
                                "$stdDevSamp": "$value",
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
        {"_id": 1, "partition": "A", "value": 10, "stdDev": None},
        {"_id": 2, "partition": "A", "value": 20, "stdDev": 7.0710678118654755},
        {"_id": 3, "partition": "A", "value": 30, "stdDev": 10.0},
    ]
    assertSuccess(result, expected, msg="Should support $stdDevSamp window operator")
