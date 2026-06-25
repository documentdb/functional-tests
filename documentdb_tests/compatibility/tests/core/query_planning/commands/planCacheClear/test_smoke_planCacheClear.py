"""
Smoke test for planCacheClear command.

Tests basic planCacheClear command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_planCacheClear(collection):
    """Test basic planCacheClear command behavior."""
    result = execute_command(collection, {"planCacheClear": collection.name})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support planCacheClear command")
