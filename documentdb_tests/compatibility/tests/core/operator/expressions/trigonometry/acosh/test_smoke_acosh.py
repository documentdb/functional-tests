"""
Smoke test for $acosh expression.

Tests basic $acosh expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_acosh(collection):
    """Test basic $acosh expression behavior."""
    collection.insert_many([{"_id": 1, "value": 1}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$acosh": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": 0.0}]
    assertSuccess(result, expected, msg="Should support $acosh expression")
