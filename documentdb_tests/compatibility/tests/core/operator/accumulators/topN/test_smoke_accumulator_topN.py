"""
Smoke test for $topN accumulator.

Tests basic $topN accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_topN(collection):
    """Test basic $topN accumulator behavior."""
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
                        "topTwo": {"$topN": {"n": 2, "sortBy": {"value": -1}, "output": "$value"}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "topTwo": [30, 20]}]
    assertSuccess(result, expected, msg="Should support $topN accumulator")
