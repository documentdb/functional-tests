"""
Smoke test for $zip expression.

Tests basic $zip expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_zip(collection):
    """Test basic $zip expression behavior."""
    collection.insert_many(
        [{"_id": 1, "a": [1, 2], "b": [10, 20]}, {"_id": 2, "a": [3, 4], "b": [30, 40]}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"zipped": {"$zip": {"inputs": ["$a", "$b"]}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "zipped": [[1, 10], [2, 20]]}, {"_id": 2, "zipped": [[3, 30], [4, 40]]}]
    assertSuccess(result, expected, msg="Should support $zip expression")
