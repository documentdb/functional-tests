"""
Smoke test for materialized-views.

Tests basic materialized view functionality using $merge stage.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_materialized_views(collection):
    """Test basic materialized view creation using $merge."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "value": 10.0},
            {"_id": 2, "category": "A", "value": 20.0},
            {"_id": 3, "category": "B", "value": 30.0},
        ]
    )

    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$category", "total": {"$sum": "$value"}}},
                {"$merge": {"into": f"{collection.name}_view", "whenMatched": "replace"}},
            ],
            "cursor": {},
        },
    )

    result = execute_command(collection, {"find": f"{collection.name}_view", "sort": {"_id": 1}})

    expected = [{"_id": "A", "total": 30.0}, {"_id": "B", "total": 30.0}]
    assertSuccess(result, expected, msg="Should support creating materialized views with $merge")
