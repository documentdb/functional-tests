"""
Smoke test for createUser command.

Tests basic createUser functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_createUser(collection):
    """Test basic createUser behavior."""
    user_name = f"{collection.name}_test_user"

    result = execute_admin_command(
        collection, {"createUser": user_name, "pwd": "testPassword", "roles": []}
    )

    execute_admin_command(collection, {"dropUser": user_name})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support createUser command")
