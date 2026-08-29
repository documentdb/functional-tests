"""
Smoke test for dbStats command.

Tests basic dbStats command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_dbStats(collection):
    """Test basic dbStats command behavior."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(collection, {"dbStats": 1})

    assertCommandSupported(result, msg="Should support dbStats command")
