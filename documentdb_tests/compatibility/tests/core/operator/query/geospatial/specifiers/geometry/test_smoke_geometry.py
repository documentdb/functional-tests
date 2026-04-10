"""
Smoke test for $geometry geospatial specifier.

Tests basic $geometry functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_geometry(collection):
    """Test basic $geometry geospatial specifier behavior."""
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
                    "$geoWithin": {
                        "$geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-1, -1], [5, -1], [5, 5], [-1, 5], [-1, -1]]],
                        }
                    }
                }
            },
        },
    )

    expected = [
        {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
    ]
    assertSuccess(result, expected, msg="Should support $geometry geospatial specifier")
