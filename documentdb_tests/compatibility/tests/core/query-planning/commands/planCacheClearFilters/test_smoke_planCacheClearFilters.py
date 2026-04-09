"""
Smoke test for planCacheClearFilters command.

Tests basic planCacheClearFilters command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_planCacheClearFilters(collection):
    """Test basic planCacheClearFilters command behavior."""
    result = execute_command(collection, {"planCacheClearFilters": collection.name})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support planCacheClearFilters command")
