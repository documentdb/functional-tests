"""
Smoke test for $querySettings stage.

Tests basic $querySettings stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_querySettings(collection):
    """Test basic $querySettings stage behavior."""
    result = execute_admin_command(
        collection, {"aggregate": 1, "pipeline": [{"$querySettings": {}}], "cursor": {}}
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $querySettings stage")
