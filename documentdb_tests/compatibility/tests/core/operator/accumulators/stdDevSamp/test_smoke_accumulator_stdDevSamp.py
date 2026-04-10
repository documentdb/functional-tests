"""
Smoke test for $stdDevSamp accumulator.

Tests basic $stdDevSamp accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_stdDevSamp(collection):
    """Test basic $stdDevSamp accumulator behavior."""
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
            "pipeline": [{"$group": {"_id": "$category", "stdDev": {"$stdDevSamp": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "stdDev": 10.0}]
    assertSuccess(result, expected, msg="Should support $stdDevSamp accumulator")
