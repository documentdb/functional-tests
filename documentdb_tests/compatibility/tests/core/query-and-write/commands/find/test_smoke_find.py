"""
Smoke test for find command.

Tests basic find command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_find(collection):
    """Test basic find command behavior."""
    collection.insert_many([{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "Bob"}])

    result = execute_command(collection, {"find": collection.name})

    expected = [{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "Bob"}]
    assertSuccess(result, expected, msg="Should support find command")
