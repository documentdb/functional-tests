"""
Smoke test for $changeStream system stage.

Tests basic $changeStream system stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_changeStream(collection):
    """Test basic $changeStream system stage behavior."""
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$changeStream": {}}], "cursor": {}},
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $changeStream system stage")
