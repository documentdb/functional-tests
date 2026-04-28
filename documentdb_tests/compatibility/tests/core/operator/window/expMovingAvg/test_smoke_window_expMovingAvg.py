"""
Smoke test for $expMovingAvg window operator.

Tests basic $expMovingAvg window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_expMovingAvg(collection):
    """Test basic $expMovingAvg window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "stock": "ABC", "price": 10},
            {"_id": 2, "stock": "ABC", "price": 12},
            {"_id": 3, "stock": "ABC", "price": 15},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$stock",
                        "sortBy": {"_id": 1},
                        "output": {"expMovingAvg": {"$expMovingAvg": {"input": "$price", "N": 2}}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "stock": "ABC", "price": 10, "expMovingAvg": 10.0},
        {"_id": 2, "stock": "ABC", "price": 12, "expMovingAvg": 11.333333333333334},
        {"_id": 3, "stock": "ABC", "price": 15, "expMovingAvg": 13.777777777777779},
    ]
    assertSuccess(result, expected, msg="Should support $expMovingAvg window operator")
