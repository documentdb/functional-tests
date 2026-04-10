"""
Smoke test for $centerSphere geospatial specifier.

Tests basic $centerSphere functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_centerSphere(collection):
    """Test basic $centerSphere geospatial specifier behavior."""
    collection.insert_many(
        [{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [1, 1]}, {"_id": 3, "loc": [10, 10]}]
    )

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.1]}}},
        },
    )

    expected = [{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [1, 1]}]
    assertSuccess(result, expected, msg="Should support $centerSphere geospatial specifier")
