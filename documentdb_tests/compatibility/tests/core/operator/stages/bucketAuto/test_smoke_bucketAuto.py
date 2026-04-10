"""
Smoke test for $bucketAuto aggregation stage.

Tests basic $bucketAuto aggregation functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_bucketAuto(collection):
    """Test basic $bucketAuto aggregation behavior."""
    collection.insert_many(
        [
            {"_id": 1, "price": 5},
            {"_id": 2, "price": 15},
            {"_id": 3, "price": 25},
            {"_id": 4, "price": 35},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$bucketAuto": {"groupBy": "$price", "buckets": 2}}],
            "cursor": {},
        },
    )

    expected = [
        {"_id": {"min": 5, "max": 25}, "count": 2},
        {"_id": {"min": 25, "max": 35}, "count": 2},
    ]
    assertSuccess(result, expected, msg="Should support $bucketAuto aggregation stage")
