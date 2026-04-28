"""
Smoke test for $linearFill window operator.

Tests basic $linearFill window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_linearFill(collection):
    """Test basic $linearFill window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "time": 1, "value": 10},
            {"_id": 2, "time": 2, "value": None},
            {"_id": 3, "time": 3, "value": 20},
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
                        "output": {"filledValue": {"$linearFill": "$value"}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "time": 1, "value": 10, "filledValue": 10},
        {"_id": 2, "time": 2, "value": None, "filledValue": 15.0},
        {"_id": 3, "time": 3, "value": 20, "filledValue": 20},
    ]
    assertSuccess(result, expected, msg="Should support $linearFill window operator")
