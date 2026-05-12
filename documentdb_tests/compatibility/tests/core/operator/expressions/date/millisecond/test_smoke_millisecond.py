"""
Smoke test for $millisecond expression.

Tests basic $millisecond expression functionality.
"""

from datetime import datetime, timezone

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_millisecond(collection):
    """Test basic $millisecond expression behavior."""
    collection.insert_many(
        [{"_id": 1, "date": datetime(2024, 1, 15, 10, 30, 45, 123000, tzinfo=timezone.utc)}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"millisecond": {"$millisecond": "$date"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "millisecond": 123}]
    assertSuccess(result, expected, msg="Should support $millisecond expression")
