"""
Smoke test for $minN window operator.

Tests basic $minN window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_minN(collection):
    """Test basic $minN window operator behavior."""
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
                            "minValues": {
                                "$minN": {"input": "$value", "n": 2},
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
        {"_id": 1, "partition": "A", "value": 30, "minValues": [30]},
        {"_id": 2, "partition": "A", "value": 10, "minValues": [10, 30]},
        {"_id": 3, "partition": "A", "value": 20, "minValues": [10, 20]},
    ]
    assertSuccess(result, expected, msg="Should support $minN window operator")
