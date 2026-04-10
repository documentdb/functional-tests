"""
Smoke test for $avg expression accumulator.

Tests basic $avg expression accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_avg(collection):
    """Test basic $avg expression accumulator behavior."""
    collection.insert_many([{"_id": 1, "values": [10, 20, 30]}, {"_id": 2, "values": [5, 15, 25]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"average": {"$avg": "$values"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "average": 20.0}, {"_id": 2, "average": 15.0}]
    assertSuccess(result, expected, msg="Should support $avg expression accumulator")
