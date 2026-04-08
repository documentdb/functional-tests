"""
Smoke test for $project stage.

Tests basic $project functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_project(collection):
    """Test basic $project behavior."""
    collection.insert_many(
        [
            {"_id": 1, "name": "Alice", "age": 30, "city": "NYC"},
            {"_id": 2, "name": "Bob", "age": 25, "city": "LA"},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"name": 1, "age": 1}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "name": "Alice", "age": 30}, {"_id": 2, "name": "Bob", "age": 25}]
    assertSuccess(result, expected, msg="Should support $project stage")
