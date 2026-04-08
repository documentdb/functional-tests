"""
Smoke test for $last expression accumulator.

Tests basic $last expression accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_last(collection):
    """Test basic $last expression accumulator behavior."""
    collection.insert_many([{"_id": 1, "values": [10, 20, 30]}, {"_id": 2, "values": [5, 15, 25]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"lastValue": {"$last": "$values"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "lastValue": 30}, {"_id": 2, "lastValue": 25}]
    assertSuccess(result, expected, msg="Should support $last expression accumulator")
