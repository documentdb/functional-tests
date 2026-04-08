"""
Smoke test for $size query operator.

Tests basic $size query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_size(collection):
    """Test basic $size query operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "items": ["apple", "banana"]},
            {"_id": 2, "items": ["apple", "banana", "orange"]},
            {"_id": 3, "items": ["apple"]},
        ]
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"items": {"$size": 2}}}
    )

    expected = [{"_id": 1, "items": ["apple", "banana"]}]
    assertSuccess(result, expected, msg="Should support $size query operator")
