"""Tests for dataSize command estimate parameter."""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.admin


def test_dataSize_estimate_true(collection):
    """Test dataSize with estimate: true returns ok: 1."""
    collection.insert_many([{"_id": i, "data": "x" * 100} for i in range(10)])
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "estimate": True})
    assertSuccessPartial(result, {"ok": 1.0}, msg="estimate true should succeed")


def test_dataSize_estimate_false(collection):
    """Test dataSize with estimate: false returns exact size (default)."""
    collection.insert_many([{"_id": i} for i in range(10)])
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "estimate": False})
    assertSuccessPartial(
        result, {"ok": 1.0, "numObjects": Int64(10)}, msg="estimate false should return exact"
    )


def test_dataSize_estimate_returns_numObjects(collection):
    """Test dataSize with estimate: true returns correct numObjects."""
    collection.insert_many([{"_id": i} for i in range(20)])
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "estimate": True})
    assertSuccessPartial(
        result, {"numObjects": Int64(20)}, msg="estimate should return correct numObjects"
    )
