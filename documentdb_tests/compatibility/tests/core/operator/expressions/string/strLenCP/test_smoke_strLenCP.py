"""
Smoke test for $strLenCP expression.

Tests basic $strLenCP expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_strLenCP(collection):
    """Test basic $strLenCP expression behavior."""
    collection.insert_many([{"_id": 1, "text": "Hello"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"length": {"$strLenCP": "$text"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "length": 5}]
    assertSuccess(result, expected, msg="Should support $strLenCP expression")
