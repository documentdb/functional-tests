"""Tests for capped collection convertToCapped behaviors."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertProperties, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq


# Property [Convert Max Ignored]: convertToCapped does not store the max
# parameter in collection metadata.
@pytest.mark.collection_mgmt
def test_capped_convert_max_ignored(database_client, collection):
    """Test that convertToCapped ignores the max parameter."""
    name = f"{collection.name}_conv"
    database_client.create_collection(name)
    database_client[name].insert_many([{"_id": i} for i in range(5)])
    execute_command(database_client[name], {"convertToCapped": name, "size": 100_000, "max": 2})
    result = execute_command(database_client[name], {"collStats": name})
    assertProperties(
        result,
        {"max": Eq(0)},
        msg="convertToCapped should not store the max parameter",
        raw_res=True,
    )


# Property [Convert Max Not Enforced]: the max parameter passed to
# convertToCapped is not enforced on subsequent inserts.
@pytest.mark.collection_mgmt
def test_capped_convert_max_not_enforced(database_client, collection):
    """Test that max from convertToCapped is not enforced on inserts."""
    name = f"{collection.name}_conv"
    database_client.create_collection(name)
    database_client[name].insert_many([{"_id": i} for i in range(5)])
    execute_command(database_client[name], {"convertToCapped": name, "size": 100_000, "max": 2})
    database_client[name].insert_many([{"_id": i} for i in range(5, 15)])
    result = execute_command(database_client[name], {"find": name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": i} for i in range(15)],
        msg="convertToCapped max should not limit subsequent inserts",
    )


# Property [Convert Drops Secondary Indexes]: all secondary indexes are dropped
# during conversion and only the _id index survives.
@pytest.mark.collection_mgmt
def test_capped_convert_index_drop(database_client, collection):
    """Test that convertToCapped drops secondary indexes."""
    name = f"{collection.name}_conv"
    database_client.create_collection(name)
    coll = database_client[name]
    coll.insert_many([{"_id": i, "x": i, "y": str(i)} for i in range(5)])
    coll.create_index("x")
    coll.create_index("y")
    execute_command(coll, {"convertToCapped": name, "size": 100_000})
    result = execute_command(coll, {"listIndexes": name})
    assertSuccess(
        result,
        ["_id_"],
        msg="convertToCapped should drop all secondary indexes",
        raw_res=True,
        transform=lambda r: [idx["name"] for idx in r["cursor"]["firstBatch"]],
    )


# Property [Convert Order Preservation]: insertion order is preserved for
# retained documents after conversion.
@pytest.mark.collection_mgmt
def test_capped_convert_order(database_client, collection):
    """Test that convertToCapped preserves insertion order."""
    name = f"{collection.name}_conv"
    database_client.create_collection(name)
    database_client[name].insert_many([{"_id": 5}, {"_id": 2}, {"_id": 8}, {"_id": 1}, {"_id": 3}])
    execute_command(database_client[name], {"convertToCapped": name, "size": 100_000})
    result = execute_command(database_client[name], {"find": name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 5}, {"_id": 2}, {"_id": 8}, {"_id": 1}, {"_id": 3}],
        msg="convertToCapped should preserve insertion order for retained documents",
    )
