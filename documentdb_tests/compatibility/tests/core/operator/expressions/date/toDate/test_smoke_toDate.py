"""
Smoke test for $toDate expression.

Tests basic $toDate expression functionality.
"""

from datetime import datetime

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_toDate(collection):
    """Test basic $toDate expression behavior."""
    collection.insert_many([{"_id": 1, "timestamp": 1705315845000}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"date": {"$toDate": "$timestamp"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "date": datetime(2024, 1, 15, 10, 50, 45)}]
    assertSuccess(result, expected, msg="Should support $toDate expression")
