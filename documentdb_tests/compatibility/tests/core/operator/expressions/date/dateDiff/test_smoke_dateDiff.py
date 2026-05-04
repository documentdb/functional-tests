"""
Smoke test for $dateDiff expression.

Tests basic $dateDiff expression functionality.
"""

from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_dateDiff(collection):
    """Test basic $dateDiff expression behavior."""
    collection.insert_many(
        [
            {
                "_id": 1,
                "startDate": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                "endDate": datetime(2024, 1, 6, 0, 0, 0, tzinfo=timezone.utc),
            }
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "diff": {
                            "$dateDiff": {
                                "startDate": "$startDate",
                                "endDate": "$endDate",
                                "unit": "day",
                            }
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "diff": Int64(5)}]
    assertSuccess(result, expected, msg="Should support $dateDiff expression")
