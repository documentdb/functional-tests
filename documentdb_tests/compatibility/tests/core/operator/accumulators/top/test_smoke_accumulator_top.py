"""
Smoke test for $top accumulator.

Tests basic $top accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_top(collection):
    """Test basic $top accumulator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "value": 10},
            {"_id": 2, "category": "A", "value": 30},
            {"_id": 3, "category": "A", "value": 20},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$group": {
                        "_id": "$category",
                        "top": {"$top": {"sortBy": {"value": -1}, "output": "$value"}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "top": 30}]
    assertSuccess(result, expected, msg="Should support $top accumulator")
