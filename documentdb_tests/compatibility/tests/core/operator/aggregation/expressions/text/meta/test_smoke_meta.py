"""
Smoke test for $meta expression.

Tests basic $meta expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_meta(collection):
    """Test basic $meta expression behavior."""
    collection.create_index([("description", "text")])
    collection.insert_many([{"_id": 1, "description": "mongodb database"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"$text": {"$search": "mongodb"}}},
                {"$project": {"score": {"$meta": "textScore"}}},
            ],
            "cursor": {},
        },
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $meta expression")
