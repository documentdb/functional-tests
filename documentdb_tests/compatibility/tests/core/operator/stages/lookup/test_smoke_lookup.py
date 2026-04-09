"""
Smoke test for $lookup stage.

Tests basic $lookup functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_lookup(collection):
    """Test basic $lookup behavior."""
    other_collection_name = f"{collection.name}_other"

    collection.insert_many([{"_id": 1, "item": "A"}, {"_id": 2, "item": "B"}])

    collection.database[other_collection_name].drop()
    collection.database[other_collection_name].insert_many(
        [
            {"_id": 1, "item": "A", "description": "Item A"},
            {"_id": 2, "item": "B", "description": "Item B"},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": other_collection_name,
                        "localField": "item",
                        "foreignField": "item",
                        "as": "details",
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "item": "A", "details": [{"_id": 1, "item": "A", "description": "Item A"}]},
        {"_id": 2, "item": "B", "details": [{"_id": 2, "item": "B", "description": "Item B"}]},
    ]
    assertSuccess(result, expected, msg="Should support $lookup stage")
