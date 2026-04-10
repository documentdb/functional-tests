"""
Smoke test for $setUnion accumulator.

Tests basic $setUnion accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_setUnion(collection):
    """Test basic $setUnion accumulator behavior."""
    collection.insert_many([{"_id": 1, "category": "A", "values": [1]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": "$category", "union": {"$setUnion": "$values"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "union": [1]}]
    assertSuccess(result, expected, msg="Should support $setUnion accumulator")
