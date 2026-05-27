"""Tests for dataSize command keyPattern and min/max parameters."""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.admin


def test_dataSize_keyPattern_id(collection):
    """Test dataSize with keyPattern: {_id: 1} succeeds."""
    collection.insert_many([{"_id": i, "x": i} for i in range(10)])
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "keyPattern": {"_id": 1}})
    assertSuccessPartial(result, {"ok": 1.0}, msg="keyPattern _id should succeed")


def test_dataSize_keyPattern_with_min_max(collection):
    """Test dataSize with keyPattern + min + max returns subset."""
    collection.insert_many([{"_id": i, "x": i} for i in range(100)])
    collection.create_index("x")
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(
        collection,
        {"dataSize": ns, "keyPattern": {"x": 1}, "min": {"x": 10}, "max": {"x": 50}},
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="keyPattern with min/max should succeed")


def test_dataSize_keyPattern_min_max_no_match(collection):
    """Test dataSize with min/max where no documents match returns 0."""
    collection.insert_many([{"_id": i, "x": i} for i in range(10)])
    collection.create_index("x")
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(
        collection,
        {"dataSize": ns, "keyPattern": {"x": 1}, "min": {"x": 1000}, "max": {"x": 2000}},
    )
    assertSuccessPartial(result, {"numObjects": Int64(0)}, msg="No match should return 0")


def test_dataSize_keyPattern_without_min_max(collection):
    """Test dataSize with keyPattern only (without min/max) succeeds."""
    collection.insert_many([{"_id": i, "x": i} for i in range(10)])
    collection.create_index("x")
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns, "keyPattern": {"x": 1}})
    assertSuccessPartial(result, {"ok": 1.0}, msg="keyPattern without min/max should succeed")


def test_dataSize_min_equal_max(collection):
    """Test dataSize with min equal to max returns 0."""
    collection.insert_many([{"_id": i, "x": i} for i in range(10)])
    collection.create_index("x")
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(
        collection,
        {"dataSize": ns, "keyPattern": {"x": 1}, "min": {"x": 5}, "max": {"x": 5}},
    )
    assertSuccessPartial(result, {"numObjects": Int64(0)}, msg="min==max should return 0")
