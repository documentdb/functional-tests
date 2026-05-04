"""
Smoke test for $month expression.

Tests basic $month expression functionality.
"""

from datetime import datetime, timezone

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_month(collection):
    """Test basic $month expression behavior."""
    collection.insert_many(
        [{"_id": 1, "date": datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"month": {"$month": "$date"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "month": 1}]
    assertSuccess(result, expected, msg="Should support $month expression")
