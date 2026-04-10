"""
Smoke test for count command.

Tests basic count command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_count(collection):
    """Test basic count command behavior."""
    collection.insert_many(
        [
            {"_id": 1, "status": "active"},
            {"_id": 2, "status": "inactive"},
            {"_id": 3, "status": "active"},
        ]
    )

    result = execute_command(collection, {"count": collection.name, "query": {"status": "active"}})

    expected = {"n": 2, "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support count command")
