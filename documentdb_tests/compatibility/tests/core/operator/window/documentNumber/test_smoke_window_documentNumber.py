"""
Smoke test for $documentNumber window operator.

Tests basic $documentNumber window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_documentNumber(collection):
    """Test basic $documentNumber window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "partition": "A", "value": 10},
            {"_id": 2, "partition": "A", "value": 20},
            {"_id": 3, "partition": "A", "value": 30},
            {"_id": 4, "partition": "B", "value": 40},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {"docNumber": {"$documentNumber": {}}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "partition": "A", "value": 10, "docNumber": 1},
        {"_id": 2, "partition": "A", "value": 20, "docNumber": 2},
        {"_id": 3, "partition": "A", "value": 30, "docNumber": 3},
        {"_id": 4, "partition": "B", "value": 40, "docNumber": 1},
    ]
    assertSuccess(result, expected, msg="Should support $documentNumber window operator")
