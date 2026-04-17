"""
Smoke test for revokeRolesFromRole command.

Tests basic revokeRolesFromRole functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_revokeRolesFromRole(collection):
    """Test basic revokeRolesFromRole behavior."""
    role_name = f"{collection.name}_test_role"

    execute_admin_command(
        collection,
        {"createRole": role_name, "privileges": [], "roles": [{"role": "read", "db": "test"}]},
    )

    result = execute_admin_command(
        collection,
        {"revokeRolesFromRole": role_name, "roles": [{"role": "read", "db": "test"}]},
    )

    execute_admin_command(collection, {"dropRole": role_name})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support revokeRolesFromRole command")
