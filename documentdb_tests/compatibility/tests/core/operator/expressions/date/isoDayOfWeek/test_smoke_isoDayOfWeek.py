"""
Smoke test for $isoDayOfWeek expression.

Tests basic $isoDayOfWeek expression functionality.
"""

from datetime import datetime

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_isoDayOfWeek(collection):
    """Test basic $isoDayOfWeek expression behavior."""
    collection.insert_many([{"_id": 1, "date": datetime(2024, 1, 15, 10, 30, 45)}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isoDayOfWeek": {"$isoDayOfWeek": "$date"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "isoDayOfWeek": 1}]
    assertSuccess(result, expected, msg="Should support $isoDayOfWeek expression")
