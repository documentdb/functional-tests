"""
Smoke test for $year expression.

Tests basic $year expression functionality.
"""

from datetime import datetime

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_year(collection):
    """Test basic $year expression behavior."""
    collection.insert_many([{"_id": 1, "date": datetime(2024, 1, 15, 10, 30, 45)}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"year": {"$year": "$date"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "year": 2024}]
    assertSuccess(result, expected, msg="Should support $year expression")
