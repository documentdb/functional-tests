"""
Smoke test for $toInt expression.

Tests basic $toInt expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_toInt(collection):
    """Test basic $toInt expression behavior."""
    collection.insert_many([{"_id": 1, "value": "123"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"int": {"$toInt": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "int": 123}]
    assertSuccess(result, expected, msg="Should support $toInt expression")
