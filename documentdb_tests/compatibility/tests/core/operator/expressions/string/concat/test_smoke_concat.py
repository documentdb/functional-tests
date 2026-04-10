"""
Smoke test for $concat expression.

Tests basic $concat expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_concat(collection):
    """Test basic $concat expression behavior."""
    collection.insert_many([{"_id": 1, "first": "Hello", "second": "World"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$concat": ["$first", " ", "$second"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": "Hello World"}]
    assertSuccess(result, expected, msg="Should support $concat expression")
