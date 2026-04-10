"""
Smoke test for $polygon geospatial specifier.

Tests basic $polygon functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_polygon(collection):
    """Test basic $polygon geospatial specifier behavior."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ]
    )

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {
                    "$geoWithin": {
                        "$geometry": {
                            "type": "Polygon",
                            "coordinates": [[[0, 0], [0, 6], [6, 6], [6, 0], [0, 0]]],
                        }
                    }
                }
            },
        },
    )

    expected = [
        {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}},
        {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
    ]
    assertSuccess(result, expected, msg="Should support $polygon geospatial specifier")
