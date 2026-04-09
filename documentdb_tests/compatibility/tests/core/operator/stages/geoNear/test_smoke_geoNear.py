"""
Smoke test for $geoNear stage.

Tests basic $geoNear functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_geoNear(collection):
    """Test basic $geoNear behavior."""
    collection.create_index([("location", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "location": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "location": {"type": "Point", "coordinates": [1, 1]}},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$geoNear": {
                        "near": {"type": "Point", "coordinates": [0, 0]},
                        "distanceField": "distance",
                        "spherical": True,
                    }
                },
                {"$limit": 1},
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "location": {"type": "Point", "coordinates": [0, 0]}, "distance": 0.0}]
    assertSuccess(result, expected, msg="Should support $geoNear stage")
