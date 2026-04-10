"""
Smoke test for $max accumulator.

Tests basic $max accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_max(collection):
    """Test basic $max accumulator behavior."""
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
            "pipeline": [{"$group": {"_id": "$category", "maxValue": {"$max": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "maxValue": 30}]
    assertSuccess(result, expected, msg="Should support $max accumulator")
