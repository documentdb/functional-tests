"""
Smoke test for $first expression accumulator.

Tests basic $first expression accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_first(collection):
    """Test basic $first expression accumulator behavior."""
    collection.insert_many([{"_id": 1, "values": [10, 20, 30]}, {"_id": 2, "values": [5, 15, 25]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"firstValue": {"$first": "$values"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "firstValue": 10}, {"_id": 2, "firstValue": 5}]
    assertSuccess(result, expected, msg="Should support $first expression accumulator")
