"""
Smoke test for $currentOp system stage.

Tests basic $currentOp system stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_system_stage_currentOp(collection):
    """Test basic $currentOp system stage behavior."""
    result = execute_admin_command(
        collection, {"aggregate": 1, "pipeline": [{"$currentOp": {}}], "cursor": {}}
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $currentOp system stage")
