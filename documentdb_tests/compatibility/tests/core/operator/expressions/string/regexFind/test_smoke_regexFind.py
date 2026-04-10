"""
Smoke test for $regexFind expression.

Tests basic $regexFind expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_regexFind(collection):
    """Test basic $regexFind expression behavior."""
    collection.insert_many([{"_id": 1, "text": "Hello World"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"match": {"$regexFind": {"input": "$text", "regex": "World"}}}}
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "match": {"match": "World", "idx": 6, "captures": []}}]
    assertSuccess(result, expected, msg="Should support $regexFind expression")
