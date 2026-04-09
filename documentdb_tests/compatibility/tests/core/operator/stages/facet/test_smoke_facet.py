"""
Smoke test for $facet stage.

Tests basic $facet functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_facet(collection):
    """Test basic $facet behavior."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "price": 10},
            {"_id": 2, "category": "B", "price": 20},
            {"_id": 3, "category": "A", "price": 30},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$facet": {
                        "categoryA": [{"$match": {"category": "A"}}],
                        "highPrice": [{"$match": {"price": {"$gte": 20}}}],
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {
            "categoryA": [
                {"_id": 1, "category": "A", "price": 10},
                {"_id": 3, "category": "A", "price": 30},
            ],
            "highPrice": [
                {"_id": 2, "category": "B", "price": 20},
                {"_id": 3, "category": "A", "price": 30},
            ],
        }
    ]
    assertSuccess(result, expected, msg="Should support $facet stage")
