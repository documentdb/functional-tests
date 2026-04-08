"""
Smoke test for $bottom accumulator.

Tests basic $bottom accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_bottom(collection):
    """Test basic $bottom accumulator behavior."""
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
                {
                    "$group": {
                        "_id": "$category",
                        "bottom": {"$bottom": {"sortBy": {"value": 1}, "output": "$value"}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "bottom": 30}]
    assertSuccess(result, expected, msg="Should support $bottom accumulator")
