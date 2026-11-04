"""
Smoke test for rolesInfo command.

Tests basic rolesInfo functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_rolesInfo(collection):
    """Test basic rolesInfo behavior."""
    result = execute_admin_command(collection, {"rolesInfo": 1})

    assertCommandSupported(result, msg="Should support rolesInfo command")
