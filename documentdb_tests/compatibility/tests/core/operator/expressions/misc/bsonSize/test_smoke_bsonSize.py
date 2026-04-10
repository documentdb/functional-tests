"""
Smoke test for $bsonSize expression.

Tests basic $bsonSize expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_bsonSize(collection):
    """Test basic $bsonSize expression behavior."""
    collection.insert_many([{"_id": 1, "data": {"name": "test"}}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"size": {"$bsonSize": "$data"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "size": 20}]
    assertSuccess(result, expected, msg="Should support $bsonSize expression")
