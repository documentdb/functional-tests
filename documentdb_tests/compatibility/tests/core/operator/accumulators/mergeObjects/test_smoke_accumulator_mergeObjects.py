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
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$group": {"_id": "$category", "merged": {"$mergeObjects": "$data"}}},
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "merged": {"x": 1, "y": 2, "z": 3}}]
    assertSuccess(result, expected, msg="Should support $mergeObjects accumulator")
    actual = result["cursor"]["firstBatch"][0]
    actual_keys = list(actual["merged"].keys())
    expected_keys = list(expected[0]["merged"].keys())
    if actual_keys != expected_keys:
        raise AssertionError(
            f"[KEY_ORDER_MISMATCH] Should support $mergeObjects accumulator\n"
            f"Expected key order: {expected_keys}\n"
            f"Actual key order:   {actual_keys}"
        )
