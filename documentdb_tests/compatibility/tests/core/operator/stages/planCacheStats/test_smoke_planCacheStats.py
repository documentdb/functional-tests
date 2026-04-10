"""
Smoke test for $planCacheStats stage.

Tests basic $planCacheStats functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_planCacheStats(collection):
    """Test basic $planCacheStats behavior."""
    collection.insert_one({"_id": 1, "value": 10})

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$planCacheStats": {}}], "cursor": {}},
    )

    expected = []
    assertSuccess(result, expected, msg="Should support $planCacheStats stage")
