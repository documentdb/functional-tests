"""
Smoke test for $maxN window operator.

Tests basic $maxN window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_maxN(collection):
    """Test basic $maxN window operator behavior."""
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
                            "maxValues": {
                                "$maxN": {"input": "$value", "n": 2},
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
        {"_id": 1, "partition": "A", "value": 10, "maxValues": [10]},
        {"_id": 2, "partition": "A", "value": 30, "maxValues": [30, 10]},
        {"_id": 3, "partition": "A", "value": 20, "maxValues": [30, 20]},
    ]
    assertSuccess(result, expected, msg="Should support $maxN window operator")
