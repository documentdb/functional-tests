"""
Smoke test for $toObjectId expression.

Tests basic $toObjectId expression functionality.
"""

import pytest
from bson import ObjectId

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_toObjectId(collection):
    """Test basic $toObjectId expression behavior."""
    collection.insert_many([{"_id": 1, "value": "507f1f77bcf86cd799439011"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"oid": {"$toObjectId": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "oid": ObjectId("507f1f77bcf86cd799439011")}]
    assertSuccess(result, expected, msg="Should support $toObjectId expression")
