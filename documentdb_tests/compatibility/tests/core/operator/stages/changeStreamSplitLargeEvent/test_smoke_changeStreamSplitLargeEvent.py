"""
Smoke test for $changeStreamSplitLargeEvent stage.

Tests basic $changeStreamSplitLargeEvent stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_changeStreamSplitLargeEvent(collection):
    """Test basic $changeStreamSplitLargeEvent stage behavior."""
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$changeStream": {}}, {"$changeStreamSplitLargeEvent": {}}],
            "cursor": {},
        },
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $changeStreamSplitLargeEvent stage")
