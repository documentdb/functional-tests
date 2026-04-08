"""
Smoke test for dropDatabase command.

Tests basic dropDatabase command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_dropDatabase(collection):
    """Test basic dropDatabase command behavior."""
    collection.insert_one({"_id": 1, "name": "test"})

    result = execute_command(collection, {"dropDatabase": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support dropDatabase command")
