"""
Smoke test for $dateTrunc expression.

Tests basic $dateTrunc expression functionality.
"""

from datetime import datetime, timezone

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_dateTrunc(collection):
    """Test basic $dateTrunc expression behavior."""
    collection.insert_many(
        [{"_id": 1, "date": datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"truncated": {"$dateTrunc": {"date": "$date", "unit": "day"}}}}
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "truncated": datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)}]
    assertSuccess(result, expected, msg="Should support $dateTrunc expression")
