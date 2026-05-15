"""
Smoke test for $dateFromParts expression.

Tests basic $dateFromParts expression functionality.
"""

from datetime import datetime, timezone

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_dateFromParts(collection):
    """Test basic $dateFromParts expression behavior."""
    collection.insert_many([{"_id": 1, "year": 2024, "month": 1, "day": 15}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "date": {
                            "$dateFromParts": {"year": "$year", "month": "$month", "day": "$day"}
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "date": datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)}]
    assertSuccess(result, expected, msg="Should support $dateFromParts expression")
