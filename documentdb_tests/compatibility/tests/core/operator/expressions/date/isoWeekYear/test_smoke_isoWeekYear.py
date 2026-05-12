"""
Smoke test for $isoWeekYear expression.

Tests basic $isoWeekYear expression functionality.
"""

from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_isoWeekYear(collection):
    """Test basic $isoWeekYear expression behavior."""
    collection.insert_many(
        [{"_id": 1, "date": datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isoWeekYear": {"$isoWeekYear": "$date"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "isoWeekYear": Int64(2024)}]
    assertSuccess(result, expected, msg="Should support $isoWeekYear expression")
