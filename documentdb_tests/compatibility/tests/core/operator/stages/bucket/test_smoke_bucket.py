"""
Smoke test for $bucket aggregation stage.

Tests basic $bucket aggregation functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_bucket(collection):
    """Test basic $bucket aggregation behavior."""
    collection.insert_many(
        [{"_id": 1, "price": 5}, {"_id": 2, "price": 15}, {"_id": 3, "price": 25}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$bucket": {"groupBy": "$price", "boundaries": [0, 30], "default": "Other"}}
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 0, "count": 3}]
    assertSuccess(result, expected, msg="Should support $bucket aggregation stage")
