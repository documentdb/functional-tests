"""
Smoke test for $listClusterCatalog stage.

Tests basic $listClusterCatalog stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_listClusterCatalog(collection):
    """Test basic $listClusterCatalog stage behavior."""
    result = execute_admin_command(
        collection, {"aggregate": 1, "pipeline": [{"$listClusterCatalog": {}}], "cursor": {}}
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $listClusterCatalog stage")
