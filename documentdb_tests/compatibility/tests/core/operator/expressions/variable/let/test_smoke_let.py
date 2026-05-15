"""
Smoke test for $let variable expression.

Tests basic $let variable expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_let(collection):
    """Test basic $let variable expression behavior."""
    collection.insert_many([{"_id": 1, "price": 10.0, "quantity": 5.0}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "total": {
                            "$let": {
                                "vars": {"p": "$price", "q": "$quantity"},
                                "in": {"$multiply": ["$$p", "$$q"]},
                            }
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "total": 50.0}]
    assertSuccess(result, expected, msg="Should support $let variable expression")
