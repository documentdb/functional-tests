"""
Smoke test for $cosh expression.

Tests basic $cosh expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_cosh(collection):
    """Test basic $cosh expression behavior."""
    collection.insert_many([{"_id": 1, "value": 0}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$cosh": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": 1.0}]
    assertSuccess(result, expected, msg="Should support $cosh expression")
