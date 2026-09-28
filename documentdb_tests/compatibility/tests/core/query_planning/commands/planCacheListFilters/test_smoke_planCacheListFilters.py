"""
Smoke test for planCacheListFilters command.

Tests basic planCacheListFilters command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_planCacheListFilters(collection):
    """Test basic planCacheListFilters command behavior."""
    result = execute_command(collection, {"planCacheListFilters": collection.name})

    expected = {"filters": [], "ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support planCacheListFilters command")
