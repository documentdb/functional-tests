"""
Smoke test for planCacheSetFilter command.

Tests basic planCacheSetFilter command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_planCacheSetFilter(collection):
    """Test basic planCacheSetFilter command behavior."""
    collection.insert_one({"_id": 1, "name": "Alice"})

    result = execute_command(
        collection,
        {"planCacheSetFilter": collection.name, "query": {"_id": 1}, "indexes": [{"_id": 1}]},
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support planCacheSetFilter command")
