"""
Tests for capped collection operations.

Capped collections are fixed-size collections that maintain insertion order.
This feature may not be supported on all engines.
"""

import pytest

from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.assertions import assertSuccess


@pytest.mark.collection_mgmt
def test_create_capped_collection(collection):
    """Test creating a capped collection."""
    db = collection.database
    result = execute_command(collection, {"create": "capped_test", "capped": True, "size": 100000})
    assertSuccess(result, {"ok": 1.0}, "Should create capped collection", raw_res=True, transform=lambda r: {"ok": r["ok"]})
    db.drop_collection("capped_test")
