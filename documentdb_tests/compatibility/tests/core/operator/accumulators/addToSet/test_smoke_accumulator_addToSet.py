"""
Smoke test for $addToSet accumulator.

Tests basic $addToSet accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_addToSet(collection):
    """Test basic $addToSet accumulator behavior."""
    collection.insert_many(
        [{"_id": 1, "category": "A", "value": 10}, {"_id": 2, "category": "A", "value": 10}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": "$category", "values": {"$addToSet": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "values": [10]}]
    assertSuccess(result, expected, msg="Should support $addToSet accumulator")
