"""
Smoke test for setQuerySettings command.

Tests basic setQuerySettings command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_setQuerySettings(collection):
    """Test basic setQuerySettings command behavior."""
    collection.insert_one({"_id": 1, "name": "Alice"})

    query = {
        "find": collection.name,
        "filter": {"name": "Alice"},
        "$db": collection.database.name,
    }
    try:
        result = execute_admin_command(
            collection,
            {"setQuerySettings": query, "settings": {"queryFramework": "classic"}},
        )

        expected = {"ok": 1.0}
        assertSuccessPartial(result, expected, msg="Should support setQuerySettings command")
    finally:
        # Query settings are cluster-wide and need to be cleaned up.
        execute_admin_command(collection, {"removeQuerySettings": query})
