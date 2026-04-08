"""
Smoke test for $max expression accumulator.

Tests basic $max expression accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_max(collection):
    """Test basic $max expression accumulator behavior."""
    collection.insert_many([{"_id": 1, "values": [10, 30, 20]}, {"_id": 2, "values": [5, 25, 15]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"maxValue": {"$max": "$values"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "maxValue": 30}, {"_id": 2, "maxValue": 25}]
    assertSuccess(result, expected, msg="Should support $max expression accumulator")
