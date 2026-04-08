"""
Smoke test for $stdDevPop expression accumulator.

Tests basic $stdDevPop expression accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_stdDevPop(collection):
    """Test basic $stdDevPop expression accumulator behavior."""
    collection.insert_many([{"_id": 1, "values": [10, 20, 30]}, {"_id": 2, "values": [5, 15, 25]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"stdDev": {"$stdDevPop": "$values"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "stdDev": 8.16496580927726}, {"_id": 2, "stdDev": 8.16496580927726}]
    assertSuccess(result, expected, msg="Should support $stdDevPop expression accumulator")
