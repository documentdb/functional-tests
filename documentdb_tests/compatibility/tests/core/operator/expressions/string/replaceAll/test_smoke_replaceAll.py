"""
Smoke test for $replaceAll expression.

Tests basic $replaceAll expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_replaceAll(collection):
    """Test basic $replaceAll expression behavior."""
    collection.insert_many([{"_id": 1, "text": "cat bat cat"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "result": {
                            "$replaceAll": {"input": "$text", "find": "cat", "replacement": "dog"}
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": "dog bat dog"}]
    assertSuccess(result, expected, msg="Should support $replaceAll expression")
