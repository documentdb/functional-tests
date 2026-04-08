"""
Smoke test for $mergeObjects expression.

Tests basic $mergeObjects expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_mergeObjects(collection):
    """Test basic $mergeObjects expression behavior."""
    collection.insert_many([{"_id": 1, "obj1": {"a": 1, "b": 2}, "obj2": {"b": 3, "c": 4}}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"merged": {"$mergeObjects": ["$obj1", "$obj2"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "merged": {"a": 1, "b": 3, "c": 4}}]
    assertSuccess(result, expected, msg="Should support $mergeObjects expression")
