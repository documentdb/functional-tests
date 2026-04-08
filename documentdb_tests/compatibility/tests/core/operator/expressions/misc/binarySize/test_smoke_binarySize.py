"""
Smoke test for $binarySize expression.

Tests basic $binarySize expression functionality.
"""

import pytest
from bson import Binary

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_binarySize(collection):
    """Test basic $binarySize expression behavior."""
    collection.insert_many([{"_id": 1, "data": Binary(b"hello")}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"size": {"$binarySize": "$data"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "size": 5}]
    assertSuccess(result, expected, msg="Should support $binarySize expression")
