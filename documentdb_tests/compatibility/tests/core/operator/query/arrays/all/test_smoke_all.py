"""
Smoke test for $all query operator.

Tests basic $all query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_all(collection):
    """Test basic $all query operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "tags": ["red", "blue"]},
            {"_id": 2, "tags": ["red", "blue", "green"]},
            {"_id": 3, "tags": ["red", "yellow"]},
        ]
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"tags": {"$all": ["red", "blue"]}}}
    )

    expected = [{"_id": 1, "tags": ["red", "blue"]}, {"_id": 2, "tags": ["red", "blue", "green"]}]
    assertSuccess(result, expected, msg="Should support $all query operator")
