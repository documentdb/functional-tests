"""
Smoke test for $bottomN accumulator.

Tests basic $bottomN accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_accumulator_bottomN(collection):
    """Test basic $bottomN accumulator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "value": 10},
            {"_id": 2, "category": "A", "value": 20},
            {"_id": 3, "category": "A", "value": 30},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$group": {
                        "_id": "$category",
                        "bottomTwo": {
                            "$bottomN": {"n": 2, "sortBy": {"value": 1}, "output": "$value"}
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "bottomTwo": [20, 30]}]
    assertSuccess(result, expected, msg="Should support $bottomN accumulator")
