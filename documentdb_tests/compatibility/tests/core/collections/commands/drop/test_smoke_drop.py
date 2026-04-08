"""
Smoke test for drop command.

Tests basic drop command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_drop(collection):
    """Test basic drop command behavior."""
    collection.insert_one({"_id": 1, "name": "test"})

    result = execute_command(collection, {"drop": collection.name})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support drop command")
