"""
Smoke test for updateRole command.

Tests basic updateRole functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_updateRole(collection):
    """Test basic updateRole behavior."""
    role_name = f"{collection.name}_test_role"

    execute_admin_command(collection, {"createRole": role_name, "privileges": [], "roles": []})

    result = execute_admin_command(
        collection,
        {
            "updateRole": role_name,
            "privileges": [{"resource": {"db": "test", "collection": ""}, "actions": ["find"]}],
            "roles": [],
        },
    )

    execute_admin_command(collection, {"dropRole": role_name})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support updateRole command")
