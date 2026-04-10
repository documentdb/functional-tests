"""
Smoke test for $map expression.

Tests basic $map expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_map(collection):
    """Test basic $map expression behavior."""
    collection.insert_many([{"_id": 1, "values": [1, 2, 3]}, {"_id": 2, "values": [4, 5, 6]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "doubled": {
                            "$map": {
                                "input": "$values",
                                "as": "item",
                                "in": {"$multiply": ["$$item", 2]},
                            }
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "doubled": [2, 4, 6]}, {"_id": 2, "doubled": [8, 10, 12]}]
    assertSuccess(result, expected, msg="Should support $map expression")
