"""
Smoke test for $bottom window operator.

Tests basic $bottom window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_bottom(collection):
    """Test basic $bottom window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "partition": "A", "value": 10},
            {"_id": 2, "partition": "A", "value": 20},
            {"_id": 3, "partition": "B", "value": 30},
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
                        "sortBy": {"value": 1},
                        "output": {
                            "bottomValue": {"$bottom": {"sortBy": {"value": 1}, "output": "$value"}}
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "partition": "A", "value": 10, "bottomValue": 20},
        {"_id": 2, "partition": "A", "value": 20, "bottomValue": 20},
        {"_id": 3, "partition": "B", "value": 30, "bottomValue": 30},
    ]
    assertSuccess(result, expected, msg="Should support $bottom window operator")
