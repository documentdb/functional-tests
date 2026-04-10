"""
Smoke test for $maxDistance geospatial specifier.

Tests basic $maxDistance functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_maxDistance(collection):
    """Test basic $maxDistance geospatial specifier behavior."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ]
    )

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {
                    "$near": {
                        "$geometry": {"type": "Point", "coordinates": [0, 0]},
                        "$maxDistance": 200000,
                    }
                }
            },
        },
    )

    expected = [
        {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
    ]
    assertSuccess(result, expected, msg="Should support $maxDistance geospatial specifier")
