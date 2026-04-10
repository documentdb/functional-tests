"""
Smoke test for $replaceOne expression.

Tests basic $replaceOne expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_replaceOne(collection):
    """Test basic $replaceOne expression behavior."""
    collection.insert_many([{"_id": 1, "text": "cat bat cat"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "result": {
                            "$replaceOne": {"input": "$text", "find": "cat", "replacement": "dog"}
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": "dog bat cat"}]
    assertSuccess(result, expected, msg="Should support $replaceOne expression")
