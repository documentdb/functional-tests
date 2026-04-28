"""
Smoke test for $push window operator.

Tests basic $push window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_push(collection):
    """Test basic $push window operator behavior."""
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
                            "values": {
                                "$push": "$value",
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
        {"_id": 1, "partition": "A", "value": 10, "values": [10]},
        {"_id": 2, "partition": "A", "value": 20, "values": [10, 20]},
        {"_id": 3, "partition": "A", "value": 30, "values": [10, 20, 30]},
    ]
    assertSuccess(result, expected, msg="Should support $push window operator")
