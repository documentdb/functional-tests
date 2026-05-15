"""
Smoke test for $text query operator.

Tests basic $text query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_query_text(collection):
    """Test basic $text query operator behavior."""
    collection.create_index([("description", "text")])
    collection.insert_many([{"_id": 1, "description": "mongodb database"}])

    result = execute_command(
        collection, {"find": collection.name, "filter": {"$text": {"$search": "mongodb"}}}
    )

    expected = [{"_id": 1, "description": "mongodb database"}]
    assertSuccess(result, expected, msg="Should support $text query operator")
