"""
Smoke test for $nearSphere query operator.

Tests basic $nearSphere query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_nearSphere(collection):
    """Test basic $nearSphere query operator behavior."""
    collection.create_index([("location", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "location": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "location": {"type": "Point", "coordinates": [5, 5]}},
        ]
    )

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "location": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}
            },
        },
    )

    expected = [
        {"_id": 1, "location": {"type": "Point", "coordinates": [0, 0]}},
        {"_id": 2, "location": {"type": "Point", "coordinates": [5, 5]}},
    ]
    assertSuccess(result, expected, msg="Should support $nearSphere query operator")
