"""
Smoke test for renameCollection command.

Tests basic renameCollection command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_renameCollection(collection):
    """Test basic renameCollection command behavior."""
    collection.insert_one({"_id": 1, "name": "test"})

    result = execute_admin_command(
        collection,
        {
            "renameCollection": f"{collection.database.name}.{collection.name}",
            "to": f"{collection.database.name}.{collection.name}_renamed",
        },
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support renameCollection command")
