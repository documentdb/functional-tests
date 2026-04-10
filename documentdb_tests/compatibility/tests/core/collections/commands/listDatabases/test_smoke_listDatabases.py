"""
Smoke test for listDatabases command.

Tests basic listDatabases command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_listDatabases(collection):
    """Test basic listDatabases command behavior."""
    result = execute_admin_command(collection, {"listDatabases": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support listDatabases command")
