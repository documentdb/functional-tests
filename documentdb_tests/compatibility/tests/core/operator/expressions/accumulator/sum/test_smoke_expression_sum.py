"""
Smoke test for $sum expression accumulator.

Tests basic $sum expression accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_sum(collection):
    """Test basic $sum expression accumulator behavior."""
    collection.insert_many([{"_id": 1, "values": [10, 20, 30]}, {"_id": 2, "values": [5, 15, 25]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"total": {"$sum": "$values"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "total": 60}, {"_id": 2, "total": 45}]
    assertSuccess(result, expected, msg="Should support $sum expression accumulator")
