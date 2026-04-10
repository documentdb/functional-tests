"""
Smoke test for $maxN accumulator.

Tests basic $maxN accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_maxN(collection):
    """Test basic $maxN accumulator behavior."""
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
                {"$group": {"_id": "$category", "maxTwo": {"$maxN": {"n": 2, "input": "$value"}}}}
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "maxTwo": [30, 20]}]
    assertSuccess(result, expected, msg="Should support $maxN accumulator")
