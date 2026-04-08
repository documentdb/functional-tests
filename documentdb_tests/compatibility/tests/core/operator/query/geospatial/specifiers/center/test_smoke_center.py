"""
Smoke test for $center geospatial specifier.

Tests basic $center functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_center(collection):
    """Test basic $center geospatial specifier behavior."""
    collection.insert_many(
        [{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [1, 1]}, {"_id": 3, "loc": [5, 5]}]
    )

    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$geoWithin": {"$center": [[0, 0], 2]}}}},
    )

    expected = [{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [1, 1]}]
    assertSuccess(result, expected, msg="Should support $center geospatial specifier")
