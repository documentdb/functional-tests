"""
Smoke test for $reduce expression.

Tests basic $reduce expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_reduce(collection):
    """Test basic $reduce expression behavior."""
    collection.insert_many([{"_id": 1, "values": [1, 2, 3]}, {"_id": 2, "values": [4, 5, 6]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "sum": {
                            "$reduce": {
                                "input": "$values",
                                "initialValue": 0,
                                "in": {"$add": ["$$value", "$$this"]},
                            }
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "sum": 6}, {"_id": 2, "sum": 15}]
    assertSuccess(result, expected, msg="Should support $reduce expression")
