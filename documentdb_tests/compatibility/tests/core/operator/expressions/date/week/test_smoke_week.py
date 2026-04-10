"""
Smoke test for $week expression.

Tests basic $week expression functionality.
"""

from datetime import datetime

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_week(collection):
    """Test basic $week expression behavior."""
    collection.insert_many([{"_id": 1, "date": datetime(2024, 1, 15, 10, 30, 45)}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"week": {"$week": "$date"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "week": 2}]
    assertSuccess(result, expected, msg="Should support $week expression")
