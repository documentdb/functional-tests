"""
Smoke test for $filter expression.

Tests basic $filter expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_filter(collection):
    """Test basic $filter expression behavior."""
    collection.insert_many(
        [{"_id": 1, "values": [1, 2, 3, 4, 5]}, {"_id": 2, "values": [10, 15, 20, 25]}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "filtered": {
                            "$filter": {
                                "input": "$values",
                                "as": "item",
                                "cond": {"$gt": ["$$item", 3]},
                            }
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "filtered": [4, 5]}, {"_id": 2, "filtered": [10, 15, 20, 25]}]
    assertSuccess(result, expected, msg="Should support $filter expression")
