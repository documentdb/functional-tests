"""Smoke test for the delete command.

Tests basic delete command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_delete(collection):
    """Test basic delete command removes a single document."""
    collection.insert_many([{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}])

    result = execute_command(
        collection,
        {"delete": collection.name, "deletes": [{"q": {"_id": 1}, "limit": 1}]},
    )

    assertSuccessPartial(result, {"ok": 1.0, "n": 1}, msg="delete should remove one document")
