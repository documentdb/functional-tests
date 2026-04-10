"""
Smoke test for $mergeObjects accumulator.

Tests basic $mergeObjects accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_mergeObjects(collection):
    """Test basic $mergeObjects accumulator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "data": {"x": 1}},
            {"_id": 2, "category": "A", "data": {"y": 2}},
            {"_id": 3, "category": "A", "data": {"z": 3}},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": "$category", "merged": {"$mergeObjects": "$data"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "merged": {"x": 1, "y": 2, "z": 3}}]
    assertSuccess(result, expected, msg="Should support $mergeObjects accumulator")
