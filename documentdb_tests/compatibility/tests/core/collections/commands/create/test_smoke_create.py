"""
Smoke test for create command.

Tests basic create command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_create(collection):
    """Test basic create command behavior."""
    result = execute_command(collection, {"create": f"{collection.name}_new"})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support create command")
