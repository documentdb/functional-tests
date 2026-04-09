"""
Smoke test for grantRolesToUser command.

Tests basic grantRolesToUser functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_grantRolesToUser(collection):
    """Test basic grantRolesToUser behavior."""
    user_name = f"{collection.name}_test_user"

    execute_admin_command(collection, {"createUser": user_name, "pwd": "testPassword", "roles": []})

    result = execute_admin_command(
        collection,
        {"grantRolesToUser": user_name, "roles": [{"role": "read", "db": "test"}]},
    )

    execute_admin_command(collection, {"dropUser": user_name})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support grantRolesToUser command")
