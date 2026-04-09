"""
Smoke test for $avg window operator.

Tests basic $avg window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_avg(collection):
    """Test basic $avg window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "partition": "A", "value": 10},
            {"_id": 2, "partition": "A", "value": 20},
            {"_id": 3, "partition": "A", "value": 30},
            {"_id": 4, "partition": "B", "value": 40},
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
                        "output": {"avgValue": {"$avg": "$value"}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "partition": "A", "value": 10, "avgValue": 20.0},
        {"_id": 2, "partition": "A", "value": 20, "avgValue": 20.0},
        {"_id": 3, "partition": "A", "value": 30, "avgValue": 20.0},
        {"_id": 4, "partition": "B", "value": 40, "avgValue": 40.0},
    ]
    assertSuccess(result, expected, msg="Should support $avg window operator")
