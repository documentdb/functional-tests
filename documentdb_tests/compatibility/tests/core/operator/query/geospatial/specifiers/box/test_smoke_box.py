"""
Smoke test for $box geospatial specifier.

Tests basic $box functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_box(collection):
    """Test basic $box geospatial specifier behavior."""
    collection.insert_many(
        [{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [5, 5]}, {"_id": 3, "loc": [10, 10]}]
    )

    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"loc": {"$geoWithin": {"$box": [[0, 0], [6, 6]]}}}},
    )

    expected = [{"_id": 1, "loc": [0, 0]}, {"_id": 2, "loc": [5, 5]}]
    assertSuccess(result, expected, msg="Should support $box geospatial specifier")
