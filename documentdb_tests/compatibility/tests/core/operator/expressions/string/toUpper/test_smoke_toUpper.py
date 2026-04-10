"""
Smoke test for $toUpper expression.

Tests basic $toUpper expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_toUpper(collection):
    """Test basic $toUpper expression behavior."""
    collection.insert_many([{"_id": 1, "text": "hello"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"upper": {"$toUpper": "$text"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "upper": "HELLO"}]
    assertSuccess(result, expected, msg="Should support $toUpper expression")
