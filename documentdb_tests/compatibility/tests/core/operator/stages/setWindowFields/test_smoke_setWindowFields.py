"""
Smoke test for $setWindowFields stage.

Tests basic $setWindowFields functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_setWindowFields(collection):
    """Test basic $setWindowFields behavior."""
    collection.insert_many(
        [{"_id": 1, "value": 10}, {"_id": 2, "value": 20}, {"_id": 3, "value": 30}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {"total": {"$sum": "$value"}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "value": 10, "total": 60},
        {"_id": 2, "value": 20, "total": 60},
        {"_id": 3, "value": 30, "total": 60},
    ]
    assertSuccess(result, expected, msg="Should support $setWindowFields stage")
