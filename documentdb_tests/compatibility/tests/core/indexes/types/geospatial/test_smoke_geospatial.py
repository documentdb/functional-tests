"""
Smoke test for geospatial index type.

Tests basic geospatial index functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
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

    assertCommandSupported(result, msg="Should support geospatial index type")
