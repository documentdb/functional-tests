"""
Smoke test for $concatArrays accumulator.

Tests basic $concatArrays accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_concatArrays(collection):
    """Test basic $concatArrays accumulator behavior."""
    collection.insert_many([{"_id": 1, "category": "A", "items": [1, 2, 3, 4]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": "$category", "allItems": {"$concatArrays": "$items"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "allItems": [1, 2, 3, 4]}]
    assertSuccess(result, expected, msg="Should support $concatArrays accumulator")
