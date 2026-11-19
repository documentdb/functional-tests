"""
Smoke test for grantRolesToRole command.

Tests basic grantRolesToRole functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_grantRolesToRole(collection):
    """Test basic grantRolesToRole behavior."""
    role_name = f"{collection.name}_test_role"

    execute_admin_command(collection, {"createRole": role_name, "privileges": [], "roles": []})

    result = execute_admin_command(
        collection,
        {"grantRolesToRole": role_name, "roles": [{"role": "read", "db": "test"}]},
    )

    execute_admin_command(collection, {"dropRole": role_name})

    assertCommandSupported(result, msg="Should support grantRolesToRole command")
