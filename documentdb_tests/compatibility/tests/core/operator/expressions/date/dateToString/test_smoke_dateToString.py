"""
Smoke test for $dateToString expression.

Tests basic $dateToString expression functionality.
"""

from datetime import datetime

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_dateToString(collection):
    """Test basic $dateToString expression behavior."""
    collection.insert_many([{"_id": 1, "date": datetime(2024, 1, 15, 10, 30, 45)}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "dateString": {"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}}
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "dateString": "2024-01-15"}]
    assertSuccess(result, expected, msg="Should support $dateToString expression")
