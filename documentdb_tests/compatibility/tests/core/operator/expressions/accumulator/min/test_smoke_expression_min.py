"""
Smoke test for $min expression accumulator.

Tests basic $min expression accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_min(collection):
    """Test basic $min expression accumulator behavior."""
    collection.insert_many([{"_id": 1, "values": [30, 10, 20]}, {"_id": 2, "values": [25, 5, 15]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"minValue": {"$min": "$values"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "minValue": 10}, {"_id": 2, "minValue": 5}]
    assertSuccess(result, expected, msg="Should support $min expression accumulator")
