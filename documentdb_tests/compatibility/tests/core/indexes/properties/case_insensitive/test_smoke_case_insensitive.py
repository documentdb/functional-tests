"""
Smoke test for case-insensitive index property.

Tests basic case-insensitive index functionality using collation.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexes_case_insensitive(collection):
    """Test basic case-insensitive index behavior."""
    collection.insert_many([{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "bob"}])

    collection.create_index([("name", 1)], collation={"locale": "en", "strength": 2.0})

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"name": "ALICE"},
            "collation": {"locale": "en", "strength": 2.0},
        },
    )

    expected = [{"_id": 1, "name": "Alice"}]
    assertSuccess(result, expected, msg="Should support case-insensitive index with collation")
