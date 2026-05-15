"""
Smoke test for multikey index type.

Tests basic multikey index functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexes_multikey(collection):
    """Test basic multikey index behavior."""
    collection.insert_many(
        [{"_id": 1, "tags": ["mongodb", "database"]}, {"_id": 2, "tags": ["nosql", "database"]}]
    )

    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"tags": 1}, "name": "tags_multikey"}],
        },
    )

    expected = {
        "numIndexesBefore": 1,
        "numIndexesAfter": 2,
        "createdCollectionAutomatically": False,
        "ok": 1.0,
    }
    assertSuccessPartial(result, expected, msg="Should support multikey index type")
