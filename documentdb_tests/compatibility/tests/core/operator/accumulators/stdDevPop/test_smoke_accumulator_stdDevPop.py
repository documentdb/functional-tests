"""
Smoke test for $stdDevPop accumulator.

Tests basic $stdDevPop accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_stdDevPop(collection):
    """Test basic $stdDevPop accumulator behavior."""
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
            "pipeline": [{"$group": {"_id": "$category", "stdDev": {"$stdDevPop": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "stdDev": 8.16496580927726}]
    assertSuccess(result, expected, msg="Should support $stdDevPop accumulator")
