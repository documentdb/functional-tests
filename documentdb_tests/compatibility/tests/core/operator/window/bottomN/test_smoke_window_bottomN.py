"""
Smoke test for $bottomN window operator.

Tests basic $bottomN window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_bottomN(collection):
    """Test basic $bottomN window operator behavior."""
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
                        "sortBy": {"value": 1},
                        "output": {
                            "bottomTwo": {
                                "$bottomN": {
                                    "n": 2,
                                    "sortBy": {"value": 1},
                                    "output": "$value",
                                }
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "partition": "A", "value": 10, "bottomTwo": [20, 30]},
        {"_id": 2, "partition": "A", "value": 20, "bottomTwo": [20, 30]},
        {"_id": 3, "partition": "A", "value": 30, "bottomTwo": [20, 30]},
        {"_id": 4, "partition": "B", "value": 40, "bottomTwo": [40]},
    ]
    assertSuccess(result, expected, msg="Should support $bottomN window operator")
