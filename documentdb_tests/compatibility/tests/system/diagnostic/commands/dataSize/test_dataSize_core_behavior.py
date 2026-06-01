"""Tests for dataSize command core behavior, response structure, and namespace edge cases."""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Gte

pytestmark = pytest.mark.admin


RESPONSE_PROPERTY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "returns_size",
        checks={"size": Gte(Int64(1))},
        msg="size should be positive",
    ),
    DiagnosticTestCase(
        "returns_millis",
        checks={"millis": Gte(0)},
        msg="millis should be >= 0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_PROPERTY_TESTS))
def test_dataSize_response_properties(collection, test):
    """Test dataSize response contains expected properties."""
    collection.insert_one({"_id": 1, "data": "x" * 100})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


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


def test_dataSize_special_chars_in_collection_name(database_client):
    """Test dataSize with special characters in collection name."""
    coll_name = "test-data_size.2024"
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1, "data": "x" * 50})
    ns = f"{database_client.name}.{coll_name}"
    result = execute_command(coll, {"dataSize": ns})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Special chars in name should succeed")


def test_dataSize_long_namespace(database_client):
    """Test dataSize with a very long namespace string."""
    coll_name = "a" * 200
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1})
    ns = f"{database_client.name}.{coll_name}"
    result = execute_command(coll, {"dataSize": ns})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Long namespace should succeed")
