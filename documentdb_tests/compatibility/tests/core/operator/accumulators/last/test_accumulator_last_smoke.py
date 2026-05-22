"""
Smoke test for $last accumulator.

Tests basic $last accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_last(collection):
    """Test basic $last accumulator behavior."""
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
                {"$group": {"_id": "$category", "lastValue": {"$last": "$value"}}},
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "lastValue": 30}]
    assertSuccess(result, expected, msg="Should support $last accumulator")
