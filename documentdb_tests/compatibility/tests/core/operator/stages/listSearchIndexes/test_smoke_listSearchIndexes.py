"""
Smoke test for $listSearchIndexes stage.

Tests basic $listSearchIndexes stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.skip(reason="Requires Atlas Search configuration - not available on standard MongoDB")
def test_smoke_listSearchIndexes(collection):
    """Test basic $listSearchIndexes stage behavior."""
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$listSearchIndexes": {}}], "cursor": {}},
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $listSearchIndexes stage")
