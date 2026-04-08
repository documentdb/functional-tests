"""
Smoke test for $geoWithin query operator.

Tests basic $geoWithin query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_geoWithin(collection):
    """Test basic $geoWithin query operator behavior."""
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
                "location": {
                    "$geoWithin": {
                        "$geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
                        }
                    }
                }
            },
        },
    )

    expected = [{"_id": 1, "location": {"type": "Point", "coordinates": [0, 0]}}]
    assertSuccess(result, expected, msg="Should support $geoWithin query operator")
