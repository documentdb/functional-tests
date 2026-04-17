"""
Smoke test for delete command.

Tests basic delete command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_delete(collection):
    """Test basic delete command behavior."""
    collection.insert_many(
        [{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "Bob"}, {"_id": 3, "name": "Charlie"}]
    )

    result = execute_command(
        collection,
        {"delete": collection.name, "deletes": [{"q": {"_id": 1}, "limit": 1}]},
    )

    expected = {"ok": 1.0, "n": 1}
    assertSuccessPartial(result, expected, msg="Should support delete command")
