"""
Smoke test for $minN accumulator.

Tests basic $minN accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_minN(collection):
    """Test basic $minN accumulator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "value": 30},
            {"_id": 2, "category": "A", "value": 10},
            {"_id": 3, "category": "A", "value": 20},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$category", "minTwo": {"$minN": {"n": 2, "input": "$value"}}}}
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "minTwo": [10, 20]}]
    assertSuccess(result, expected, msg="Should support $minN accumulator")
