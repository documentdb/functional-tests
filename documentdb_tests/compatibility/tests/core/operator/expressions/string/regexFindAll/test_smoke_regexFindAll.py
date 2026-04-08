"""
Smoke test for $regexFindAll expression.

Tests basic $regexFindAll expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_regexFindAll(collection):
    """Test basic $regexFindAll expression behavior."""
    collection.insert_many([{"_id": 1, "text": "cat bat rat"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"matches": {"$regexFindAll": {"input": "$text", "regex": "[a-z]at"}}}}
            ],
            "cursor": {},
        },
    )

    expected = [
        {
            "_id": 1,
            "matches": [
                {"match": "cat", "idx": 0, "captures": []},
                {"match": "bat", "idx": 4, "captures": []},
                {"match": "rat", "idx": 8, "captures": []},
            ],
        }
    ]
    assertSuccess(result, expected, msg="Should support $regexFindAll expression")
