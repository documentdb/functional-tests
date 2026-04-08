"""
Smoke test for $percentile expression accumulator.

Tests basic $percentile expression accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_percentile(collection):
    """Test basic $percentile expression accumulator behavior."""
    collection.insert_many([{"_id": 1, "values": [10, 20, 30]}, {"_id": 2, "values": [5, 15, 25]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "p50": {
                            "$percentile": {"input": "$values", "p": [0.5], "method": "approximate"}
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "p50": [20.0]}, {"_id": 2, "p50": [15.0]}]
    assertSuccess(result, expected, msg="Should support $percentile expression accumulator")
