"""
Smoke test for $redact stage.

Tests basic $redact functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_redact(collection):
    """Test basic $redact behavior."""
    collection.insert_many([{"_id": 1, "level": 5}, {"_id": 2, "level": 3}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$redact": {"$cond": [{"$gte": ["$level", 5]}, "$$KEEP", "$$PRUNE"]}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "level": 5}]
    assertSuccess(result, expected, msg="Should support $redact stage")
