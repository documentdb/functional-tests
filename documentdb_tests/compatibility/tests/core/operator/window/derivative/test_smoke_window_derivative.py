"""
Smoke test for $derivative window operator.

Tests basic $derivative window operator functionality.
"""

from datetime import datetime

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_derivative(collection):
    """Test basic $derivative window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "partition": "A", "time": datetime(2021, 1, 1, 0, 0, 0), "value": 10},
            {"_id": 2, "partition": "A", "time": datetime(2021, 1, 1, 0, 0, 1), "value": 20},
            {"_id": 3, "partition": "A", "time": datetime(2021, 1, 1, 0, 0, 2), "value": 35},
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
                        "sortBy": {"time": 1},
                        "output": {
                            "rate": {
                                "$derivative": {"input": "$value", "unit": "second"},
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
        {
            "_id": 1,
            "partition": "A",
            "time": datetime(2021, 1, 1, 0, 0, 0),
            "value": 10,
            "rate": None,
        },
        {
            "_id": 2,
            "partition": "A",
            "time": datetime(2021, 1, 1, 0, 0, 1),
            "value": 20,
            "rate": 10.0,
        },
        {
            "_id": 3,
            "partition": "A",
            "time": datetime(2021, 1, 1, 0, 0, 2),
            "value": 35,
            "rate": 12.5,
        },
    ]
    assertSuccess(result, expected, msg="Should support $derivative window operator")
