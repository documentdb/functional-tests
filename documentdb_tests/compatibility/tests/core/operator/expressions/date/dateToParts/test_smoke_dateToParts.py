"""
Smoke test for $dateToParts expression.

Tests basic $dateToParts expression functionality.
"""

from datetime import datetime

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_dateToParts(collection):
    """Test basic $dateToParts expression behavior."""
    collection.insert_many([{"_id": 1, "date": datetime(2024, 1, 15, 10, 30, 45)}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"parts": {"$dateToParts": {"date": "$date"}}}}],
            "cursor": {},
        },
    )

    expected = [
        {
            "_id": 1,
            "parts": {
                "year": 2024,
                "month": 1,
                "day": 15,
                "hour": 10,
                "minute": 30,
                "second": 45,
                "millisecond": 0,
            },
        }
    ]
    assertSuccess(result, expected, msg="Should support $dateToParts expression")
