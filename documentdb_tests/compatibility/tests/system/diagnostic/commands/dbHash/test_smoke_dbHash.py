"""
Smoke test for dbHash command.

Tests basic dbHash command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_dbHash(collection):
    """Test basic dbHash command behavior."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(collection, {"dbHash": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support dbHash command")
