"""
Smoke test for distinct command.

Tests basic distinct command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_distinct(collection):
    """Test basic distinct command behavior."""
    collection.insert_many([{"_id": 1, "category": "A"}, {"_id": 2, "category": "A"}])

    result = execute_command(collection, {"distinct": collection.name, "key": "category"})

    expected = {"values": ["A"], "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support distinct command")
