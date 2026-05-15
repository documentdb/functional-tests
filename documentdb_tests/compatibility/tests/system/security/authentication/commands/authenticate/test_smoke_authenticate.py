"""
Smoke test for authenticate command.

Tests basic authenticate functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailure
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_authenticate(collection):
    """Test basic authenticate behavior."""
    # The authenticate command is deprecated but should be recognized
    # We verify it's supported by checking it returns an auth error, not "command not found"
    result = execute_command(
        collection, {"authenticate": 1, "mechanism": "SCRAM-SHA-256", "user": "nonexistentuser"}
    )

    # Command is recognized and returns authentication error (not command not found)
    expected = {"code": 18, "msg": "Authentication failed."}
    assertFailure(result, expected, msg="Should support authenticate command")
