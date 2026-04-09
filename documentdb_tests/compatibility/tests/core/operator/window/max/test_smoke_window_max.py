"""
Smoke test for $max window operator.

Tests basic $max window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_max(collection):
    """Test basic $max window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "partition": "A", "value": 10},
            {"_id": 2, "partition": "A", "value": 30},
            {"_id": 3, "partition": "A", "value": 20},
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
                            "maxValue": {
                                "$max": "$value",
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
        {"_id": 1, "partition": "A", "value": 10, "maxValue": 10},
        {"_id": 2, "partition": "A", "value": 30, "maxValue": 30},
        {"_id": 3, "partition": "A", "value": 20, "maxValue": 30},
    ]
    assertSuccess(result, expected, msg="Should support $max window operator")
