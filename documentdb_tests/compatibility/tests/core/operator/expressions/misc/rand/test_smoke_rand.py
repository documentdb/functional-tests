"""
Smoke test for $rand expression.

Tests basic $rand expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_rand(collection):
    """Test basic $rand expression behavior."""
    collection.insert_many([{"_id": 1}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isValid": {"$lt": [{"$rand": {}}, 1.0]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "isValid": True}]
    assertSuccess(result, expected, msg="Should support $rand expression")
