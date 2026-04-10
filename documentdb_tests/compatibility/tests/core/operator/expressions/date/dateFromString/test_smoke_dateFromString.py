"""
Smoke test for $dateFromString expression.

Tests basic $dateFromString expression functionality.
"""

from datetime import datetime

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_dateFromString(collection):
    """Test basic $dateFromString expression behavior."""
    collection.insert_many([{"_id": 1, "dateString": "2024-01-15"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"date": {"$dateFromString": {"dateString": "$dateString"}}}}
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "date": datetime(2024, 1, 15, 0, 0, 0)}]
    assertSuccess(result, expected, msg="Should support $dateFromString expression")
