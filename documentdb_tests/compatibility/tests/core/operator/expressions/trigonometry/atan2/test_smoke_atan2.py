"""
Smoke test for $atan2 expression.

Tests basic $atan2 expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_atan2(collection):
    """Test basic $atan2 expression behavior."""
    collection.insert_many([{"_id": 1, "y": 0, "x": 1}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$atan2": ["$y", "$x"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": 0.0}]
    assertSuccess(result, expected, msg="Should support $atan2 expression")
