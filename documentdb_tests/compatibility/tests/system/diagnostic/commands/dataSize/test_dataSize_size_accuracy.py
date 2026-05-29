"""Tests for dataSize command size accuracy."""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Gt, Gte

pytestmark = pytest.mark.admin


def test_dataSize_large_collection(collection):
    """Test dataSize on collection with 200 documents returns correct numObjects."""
    collection.insert_many([{"_id": i, "value": i} for i in range(200)])
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns})
    assertSuccessPartial(result, {"numObjects": Int64(200)}, msg="Should report 200 objects")


def test_dataSize_large_documents_count(collection):
    """Test dataSize on collection with large documents returns correct numObjects."""
    collection.insert_many([{"_id": i, "data": "x" * 3000} for i in range(50)])
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns})
    assertSuccessPartial(result, {"numObjects": Int64(50)}, msg="Should report 50 objects")


def test_dataSize_large_documents_size(collection):
    """Test dataSize on collection with large documents returns expected minimum size."""
    collection.insert_many([{"_id": i, "data": "x" * 3000} for i in range(50)])
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns})
    assertResult(
        result,
        expected={"size": Gte(Int64(150000))},
        raw_res=True,
        msg="size should reflect large docs",
    )


def test_dataSize_indexes_dont_affect_size(collection):
    """Test dataSize is not affected by indexes."""
    collection.insert_many([{"_id": i, "x": i} for i in range(50)])
    ns = f"{collection.database.name}.{collection.name}"
    r1 = execute_command(collection, {"dataSize": ns})
    size1 = r1["size"]
    collection.create_index("x")
    r2 = execute_command(collection, {"dataSize": ns})
    assertSuccessPartial(r2, {"size": size1}, msg="Indexes should not affect dataSize")


def test_dataSize_increases_after_insert(collection):
    """Test dataSize increases after inserting documents."""
    collection.insert_one({"_id": 0})
    ns = f"{collection.database.name}.{collection.name}"
    r1 = execute_command(collection, {"dataSize": ns})
    size1 = r1["size"]
    collection.insert_many([{"_id": i, "data": "x" * 100} for i in range(1, 50)])
    r2 = execute_command(collection, {"dataSize": ns})
    assertResult(
        r2, expected={"size": Gt(size1)}, raw_res=True, msg="Size should increase after inserts"
    )
