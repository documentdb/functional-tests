"""
Smoke test for rolesInfo command.

Tests basic rolesInfo functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_rolesInfo(collection):
    """Test basic rolesInfo behavior.

    Queries rolesInfo for only the role this test creates, not the whole
    server. ``{"rolesInfo": 1}`` lists every role in the database, including
    roles that parallel tests create and drop, which makes the result
    non-deterministic. Scoping to the test's own role keeps the capability
    probe deterministic under parallel execution.
    """
    role_name = f"{collection.name}_test_role"

    execute_admin_command(collection, {"createRole": role_name, "privileges": [], "roles": []})
    try:
        result = execute_admin_command(collection, {"rolesInfo": role_name})
    finally:
        execute_admin_command(collection, {"dropRole": role_name})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support rolesInfo command")
