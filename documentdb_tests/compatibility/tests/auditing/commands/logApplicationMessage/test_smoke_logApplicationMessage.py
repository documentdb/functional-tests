"""
Smoke test for logApplicationMessage command.

Tests basic logApplicationMessage functionality.
Note: This command requires auditing to be enabled (--auditLog startup option).
On servers without auditing, it returns CommandNotFound (code 59).
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


@pytest.mark.skip(reason="Requires auditing to be enabled")
def test_smoke_logApplicationMessage(collection):
    """Test basic logApplicationMessage behavior."""
    result = execute_admin_command(collection, {"logApplicationMessage": "test message"})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support logApplicationMessage command")
