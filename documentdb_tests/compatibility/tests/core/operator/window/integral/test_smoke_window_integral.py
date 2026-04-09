"""
Smoke test for $integral window operator.

Tests basic $integral window operator functionality.
"""

from datetime import datetime

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_integral(collection):
    """Test basic $integral window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "time": datetime(2021, 1, 1, 0, 0, 0), "value": 10},
            {"_id": 2, "time": datetime(2021, 1, 1, 0, 0, 10), "value": 20},
            {"_id": 3, "time": datetime(2021, 1, 1, 0, 0, 20), "value": 30},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"time": 1},
                        "output": {
                            "integral": {
                                "$integral": {"input": "$value", "unit": "second"},
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
        {"_id": 1, "time": datetime(2021, 1, 1, 0, 0, 0), "value": 10, "integral": 0.0},
        {"_id": 2, "time": datetime(2021, 1, 1, 0, 0, 10), "value": 20, "integral": 150.0},
        {"_id": 3, "time": datetime(2021, 1, 1, 0, 0, 20), "value": 30, "integral": 400.0},
    ]
    assertSuccess(result, expected, msg="Should support $integral window operator")
