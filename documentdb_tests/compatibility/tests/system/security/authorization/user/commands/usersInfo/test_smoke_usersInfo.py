"""
Smoke test for usersInfo command.

Tests basic usersInfo functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_usersInfo(collection):
    """Test basic usersInfo behavior.

    Queries usersInfo for only the user this test creates, not the whole
    server. ``{"usersInfo": 1}`` lists every user in the database, including
    users that parallel tests create and drop, which makes the result
    non-deterministic. Scoping to the test's own user keeps the capability
    probe deterministic under parallel execution.
    """
    user_name = f"{collection.name}_test_user"

    execute_admin_command(collection, {"createUser": user_name, "pwd": "testPassword", "roles": []})
    try:
        result = execute_admin_command(collection, {"usersInfo": user_name})
    finally:
        execute_admin_command(collection, {"dropUser": user_name})

    assertCommandSupported(result, msg="Should support usersInfo command")
