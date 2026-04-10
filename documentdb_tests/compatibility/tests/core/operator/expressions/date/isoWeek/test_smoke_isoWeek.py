"""
Smoke test for $isoWeek expression.

Tests basic $isoWeek expression functionality.
"""

from datetime import datetime

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_isoWeek(collection):
    """Test basic $isoWeek expression behavior."""
    collection.insert_many([{"_id": 1, "date": datetime(2024, 1, 15, 10, 30, 45)}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isoWeek": {"$isoWeek": "$date"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "isoWeek": 3}]
    assertSuccess(result, expected, msg="Should support $isoWeek expression")
