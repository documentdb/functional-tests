"""
Smoke test for $addToSet window operator.

Tests basic $addToSet window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_addToSet(collection):
    """Test basic $addToSet window operator behavior."""
    collection.insert_many([{"_id": 1, "value": 10}, {"_id": 2, "value": 10}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {"uniqueValues": {"$addToSet": "$value"}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "value": 10, "uniqueValues": [10]},
        {"_id": 2, "value": 10, "uniqueValues": [10]},
    ]
    assertSuccess(result, expected, msg="Should support $addToSet window operator")
