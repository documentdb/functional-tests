"""
Smoke test for $min window operator.

Tests basic $min window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_min(collection):
    """Test basic $min window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "partition": "A", "value": 30},
            {"_id": 2, "partition": "A", "value": 10},
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
                            "minValue": {
                                "$min": "$value",
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
        {"_id": 1, "partition": "A", "value": 30, "minValue": 30},
        {"_id": 2, "partition": "A", "value": 10, "minValue": 10},
        {"_id": 3, "partition": "A", "value": 20, "minValue": 10},
    ]
    assertSuccess(result, expected, msg="Should support $min window operator")
