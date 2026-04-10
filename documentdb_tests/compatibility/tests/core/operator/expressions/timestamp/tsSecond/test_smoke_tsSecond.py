"""
Smoke test for $tsSecond expression.

Tests basic $tsSecond expression functionality.
"""

import pytest
from bson import Int64, Timestamp

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_tsSecond(collection):
    """Test basic $tsSecond expression behavior."""
    collection.insert_many([{"_id": 1, "ts": Timestamp(1234567890, 5)}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"second": {"$tsSecond": "$ts"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "second": Int64(1234567890)}]
    assertSuccess(result, expected, msg="Should support $tsSecond expression")
