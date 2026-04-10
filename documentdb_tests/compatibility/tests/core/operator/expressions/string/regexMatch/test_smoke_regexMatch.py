"""
Smoke test for $regexMatch expression.

Tests basic $regexMatch expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_regexMatch(collection):
    """Test basic $regexMatch expression behavior."""
    collection.insert_many([{"_id": 1, "text": "Hello123"}, {"_id": 2, "text": "Hello"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"hasDigit": {"$regexMatch": {"input": "$text", "regex": "[0-9]"}}}}
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "hasDigit": True}, {"_id": 2, "hasDigit": False}]
    assertSuccess(result, expected, msg="Should support $regexMatch expression")
