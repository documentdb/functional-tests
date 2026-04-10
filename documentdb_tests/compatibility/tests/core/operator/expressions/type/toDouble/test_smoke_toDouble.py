"""
Smoke test for $toDouble expression.

Tests basic $toDouble expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_toDouble(collection):
    """Test basic $toDouble expression behavior."""
    collection.insert_many([{"_id": 1, "value": 123}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"double": {"$toDouble": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "double": 123.0}]
    assertSuccess(result, expected, msg="Should support $toDouble expression")
