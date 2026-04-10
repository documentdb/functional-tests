"""
Smoke test for $jsonSchema query operator.

Tests basic $jsonSchema functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_jsonSchema(collection):
    """Test basic $jsonSchema query operator behavior."""
    collection.insert_many([{"_id": 1, "x": 5}, {"_id": 2, "x": "text"}, {"_id": 3, "x": 15}])

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$jsonSchema": {"properties": {"x": {"bsonType": "int"}}}},
        },
    )

    expected = [{"_id": 1, "x": 5}, {"_id": 3, "x": 15}]
    assertSuccess(result, expected, msg="Should support $jsonSchema query operator")
