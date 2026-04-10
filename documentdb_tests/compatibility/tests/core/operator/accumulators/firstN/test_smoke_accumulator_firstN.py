"""
Smoke test for $firstN accumulator.

Tests basic $firstN accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_firstN(collection):
    """Test basic $firstN accumulator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "value": 10},
            {"_id": 2, "category": "A", "value": 20},
            {"_id": 3, "category": "A", "value": 30},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"value": 1}},
                {
                    "$group": {
                        "_id": "$category",
                        "firstTwo": {"$firstN": {"n": 2, "input": "$value"}},
                    }
                },
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "firstTwo": [10, 20]}]
    assertSuccess(result, expected, msg="Should support $firstN accumulator")
