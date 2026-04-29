"""
Smoke test for bson-types.

Tests basic BSON type support including ObjectId, Date, and Binary.
"""

from datetime import datetime

import pytest
from bson import Binary, ObjectId

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_bson_types(collection):
    """Test basic BSON type storage and retrieval."""
    test_oid = ObjectId()
    test_date = datetime(2024, 1, 1, 12, 0, 0)
    test_binary = Binary(b"test data")

    collection.insert_many([{"_id": 1, "oid": test_oid, "date": test_date, "binary": test_binary}])

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})

    expected = [{"_id": 1, "oid": test_oid, "date": test_date, "binary": b"test data"}]
    assertSuccess(result, expected, msg="Should support BSON types")
