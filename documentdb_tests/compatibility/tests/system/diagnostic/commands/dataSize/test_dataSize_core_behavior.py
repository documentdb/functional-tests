"""Tests for dataSize command core behavior and response structure."""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Gte

pytestmark = pytest.mark.admin


def test_dataSize_returns_ok(collection):
    """Test dataSize on existing collection returns ok: 1."""
    collection.insert_one({"_id": 1, "x": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should return ok: 1")


def test_dataSize_returns_size(collection):
    """Test dataSize returns size as a number."""
    collection.insert_one({"_id": 1, "data": "x" * 100})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns})
    assertResult(
        result, expected={"size": Gte(Int64(1))}, raw_res=True, msg="size should be positive"
    )


def test_dataSize_returns_numObjects(collection):
    """Test dataSize returns numObjects matching document count."""
    collection.insert_many([{"_id": i} for i in range(5)])
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns})
    assertSuccessPartial(result, {"numObjects": Int64(5)}, msg="numObjects should match count")


def test_dataSize_empty_collection(database_client):
    """Test dataSize on empty collection returns size: 0, numObjects: 0."""
    database_client.create_collection("empty_ds")
    ns = f"{database_client.name}.empty_ds"
    coll = database_client["empty_ds"]
    result = execute_command(coll, {"dataSize": ns})
    assertSuccessPartial(
        result, {"size": Int64(0), "numObjects": Int64(0)}, msg="Empty should have zeros"
    )


def test_dataSize_non_existent_collection(collection):
    """Test dataSize on non-existent collection returns zeros."""
    ns = f"{collection.database.name}.nonexistent_xyz"
    result = execute_command(collection, {"dataSize": ns})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "size": Int64(0), "numObjects": Int64(0)},
        msg="Non-existent should return zeros",
    )


def test_dataSize_returns_millis(collection):
    """Test dataSize response contains millis field."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns})
    assertResult(result, expected={"millis": Gte(0)}, raw_res=True, msg="millis should be >= 0")
