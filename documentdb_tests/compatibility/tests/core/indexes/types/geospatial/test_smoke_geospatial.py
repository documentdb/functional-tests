"""
Smoke test for geospatial index type.

Tests basic geospatial index functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexes_geospatial(collection):
    """Test basic geospatial index behavior."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"location": "2dsphere"}, "name": "location_2dsphere"}],
        },
    )

    expected = {
        "numIndexesBefore": 1,
        "numIndexesAfter": 2,
        "createdCollectionAutomatically": True,
        "ok": 1.0,
    }
    assertSuccessPartial(result, expected, msg="Should support geospatial index type")
