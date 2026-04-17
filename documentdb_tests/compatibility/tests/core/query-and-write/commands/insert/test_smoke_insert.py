"""
Smoke test for insert command.

Tests basic insert command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_insert(collection):
    """Test basic insert command behavior."""
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "Bob"}],
        },
    )

    expected = {"ok": 1.0, "n": 2}
    assertSuccessPartial(result, expected, msg="Should support insert command")
