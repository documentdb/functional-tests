"""
Smoke test for $median expression accumulator.

Tests basic $median expression accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_median(collection):
    """Test basic $median expression accumulator behavior."""
    collection.insert_many([{"_id": 1, "values": [10, 20, 30]}, {"_id": 2, "values": [5, 15, 25]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "medianValue": {"$median": {"input": "$values", "method": "approximate"}}
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "medianValue": 20.0}, {"_id": 2, "medianValue": 15.0}]
    assertSuccess(result, expected, msg="Should support $median expression accumulator")
