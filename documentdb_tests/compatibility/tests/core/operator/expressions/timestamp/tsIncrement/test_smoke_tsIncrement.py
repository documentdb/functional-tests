"""
Smoke test for $tsIncrement expression.

Tests basic $tsIncrement expression functionality.
"""

import pytest
from bson import Int64, Timestamp

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_tsIncrement(collection):
    """Test basic $tsIncrement expression behavior."""
    collection.insert_many([{"_id": 1, "ts": Timestamp(1234567890, 5)}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"increment": {"$tsIncrement": "$ts"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "increment": Int64(5)}]
    assertSuccess(result, expected, msg="Should support $tsIncrement expression")
