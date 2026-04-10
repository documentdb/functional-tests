"""
Smoke test for $graphLookup stage.

Tests basic $graphLookup functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_graphLookup(collection):
    """Test basic $graphLookup behavior."""
    collection.insert_many(
        [{"_id": 1, "name": "A", "connects": 2}, {"_id": 2, "name": "B", "connects": None}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"_id": 1}},
                {
                    "$graphLookup": {
                        "from": collection.name,
                        "startWith": "$connects",
                        "connectFromField": "connects",
                        "connectToField": "_id",
                        "as": "connections",
                    }
                },
            ],
            "cursor": {},
        },
    )

    expected = [
        {
            "_id": 1,
            "name": "A",
            "connects": 2,
            "connections": [{"_id": 2, "name": "B", "connects": None}],
        }
    ]
    assertSuccess(result, expected, msg="Should support $graphLookup stage")
