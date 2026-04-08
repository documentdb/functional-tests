"""
Smoke test for $anyElementTrue expression.

Tests basic $anyElementTrue expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_anyElementTrue(collection):
    """Test basic $anyElementTrue expression behavior."""
    collection.insert_many(
        [{"_id": 1, "values": [False, False, False]}, {"_id": 2, "values": [False, True, False]}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"anyTrue": {"$anyElementTrue": "$values"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "anyTrue": False}, {"_id": 2, "anyTrue": True}]
    assertSuccess(result, expected, msg="Should support $anyElementTrue expression")
