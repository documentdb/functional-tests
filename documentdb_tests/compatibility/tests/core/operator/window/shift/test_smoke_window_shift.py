"""
Smoke test for $shift window operator.

Tests basic $shift window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_shift(collection):
    """Test basic $shift window operator behavior."""
    collection.insert_many(
        [{"_id": 1, "value": 10}, {"_id": 2, "value": 20}, {"_id": 3, "value": 30}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {"prevValue": {"$shift": {"output": "$value", "by": -1}}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "value": 10, "prevValue": None},
        {"_id": 2, "value": 20, "prevValue": 10},
        {"_id": 3, "value": 30, "prevValue": 20},
    ]
    assertSuccess(result, expected, msg="Should support $shift window operator")
