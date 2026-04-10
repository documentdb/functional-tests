"""
Smoke test for $push accumulator.

Tests basic $push accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_push(collection):
    """Test basic $push accumulator behavior."""
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
            "pipeline": [{"$group": {"_id": "$category", "values": {"$push": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "values": [10, 20, 30]}]
    assertSuccess(result, expected, msg="Should support $push accumulator")
