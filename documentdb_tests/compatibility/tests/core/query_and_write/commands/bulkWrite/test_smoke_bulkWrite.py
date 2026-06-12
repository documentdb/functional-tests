"""
Smoke test for bulkWrite command.

Tests basic bulkWrite command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_bulkWrite(collection):
    """Test basic bulkWrite command behavior."""
    result = execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1, "name": "Alice"}},
                {"insert": 0, "document": {"_id": 2, "name": "Bob"}},
            ],
            "nsInfo": [{"ns": f"{collection.database.name}.{collection.name}"}],
        },
    )

    expected = {"ok": 1.0, "nInserted": 2}
    assertSuccessPartial(result, expected, msg="Should support bulkWrite command")
