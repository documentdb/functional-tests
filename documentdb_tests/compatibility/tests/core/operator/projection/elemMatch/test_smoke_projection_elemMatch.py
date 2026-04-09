"""
Smoke test for $elemMatch projection operator.

Tests basic $elemMatch projection functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_projection_elemMatch(collection):
    """Test basic $elemMatch projection behavior."""
    collection.insert_many([{"_id": 1, "scores": [82, 85, 88]}, {"_id": 2, "scores": [75, 88, 89]}])

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "projection": {"scores": {"$elemMatch": {"$gte": 80, "$lt": 85}}},
        },
    )

    expected = [{"_id": 1, "scores": [82]}, {"_id": 2}]
    assertSuccess(result, expected, msg="Should support $elemMatch projection")
