"""
Smoke test for $dateSubtract expression.

Tests basic $dateSubtract expression functionality.
"""

from datetime import datetime, timezone

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_dateSubtract(collection):
    """Test basic $dateSubtract expression behavior."""
    collection.insert_many([{"_id": 1, "date": datetime(2024, 1, 6, 0, 0, 0, tzinfo=timezone.utc)}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "newDate": {
                            "$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 5}
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "newDate": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)}]
    assertSuccess(result, expected, msg="Should support $dateSubtract expression")
