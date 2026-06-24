"""
Smoke test for applyOps command.

Tests basic applyOps command functionality by applying a single insert
oplog entry.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.requires(change_streams=True), pytest.mark.no_parallel]


def test_smoke_applyOps(collection):
    """Test basic applyOps command behavior."""
    collection.insert_one({"_id": 0, "setup": True})

    namespace = f"{collection.database.name}.{collection.name}"
    result = execute_admin_command(
        collection,
        {
            "applyOps": [
                {
                    "op": "i",
                    "ns": namespace,
                    "o": {"_id": 1, "x": 1},
                }
            ],
        },
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support applyOps command")
