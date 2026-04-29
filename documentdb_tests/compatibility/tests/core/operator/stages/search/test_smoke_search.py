"""
Smoke test for $search stage.

Tests basic $search stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.skip(reason="Requires Atlas Search configuration - not available on standard MongoDB")
def test_smoke_search(collection):
    """Test basic $search stage behavior."""
    collection.insert_many([{"_id": 1, "title": "test document"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$search": {"text": {"query": "test", "path": "title"}}}],
            "cursor": {},
        },
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $search stage")
