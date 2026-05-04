"""
Smoke test for $searchMeta stage.

Tests basic $searchMeta stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.skip(reason="Requires Atlas Search configuration - not available on standard MongoDB")
def test_smoke_searchMeta(collection):
    """Test basic $searchMeta stage behavior."""
    collection.insert_many([{"_id": 1, "title": "test document"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$searchMeta": {"text": {"query": "test", "path": "title"}}}],
            "cursor": {},
        },
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $searchMeta stage")
