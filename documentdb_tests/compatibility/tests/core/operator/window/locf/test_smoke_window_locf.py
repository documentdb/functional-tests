"""
Smoke test for $locf window operator.

Tests basic $locf window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_locf(collection):
    """Test basic $locf window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "value": 10},
            {"_id": 2, "value": None},
            {"_id": 3, "value": None},
            {"_id": 4, "value": 20},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {"filledValue": {"$locf": "$value"}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "value": 10, "filledValue": 10},
        {"_id": 2, "value": None, "filledValue": 10},
        {"_id": 3, "value": None, "filledValue": 10},
        {"_id": 4, "value": 20, "filledValue": 20},
    ]
    assertSuccess(result, expected, msg="Should support $locf window operator")
