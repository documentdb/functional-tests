"""
Smoke test for planCacheListFilters command.

Tests basic planCacheListFilters command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_planCacheListFilters(collection):
    """Test basic planCacheListFilters command behavior."""
    result = execute_command(collection, {"planCacheListFilters": collection.name})

    assertCommandSupported(result, msg="Should support planCacheListFilters command")
