"""Tests for dbHash UUID consistency."""

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Ne

pytestmark = pytest.mark.admin


def test_dbHash_uuid_stable_across_calls(collection):
    """Test UUID for a collection remains stable across dbHash calls."""
    collection.insert_one({"_id": 1})
    r1 = execute_command(collection, {"dbHash": 1})
    uuid1 = r1["uuids"][collection.name]
    r2 = execute_command(collection, {"dbHash": 1})
    assertResult(
        r2,
        expected={"uuids": {collection.name: Eq(uuid1)}},
        raw_res=True,
        msg="UUID should be stable",
    )


def test_dbHash_uuid_changes_after_recreate(database_client):
    """Test UUID changes after dropping and recreating a collection with same name."""
    database_client.create_collection("uuid_test")
    database_client["uuid_test"].insert_one({"_id": 1})
    coll = database_client["uuid_test"]
    r1 = execute_command(coll, {"dbHash": 1})
    uuid1 = r1["uuids"]["uuid_test"]
    database_client.drop_collection("uuid_test")
    database_client.create_collection("uuid_test")
    database_client["uuid_test"].insert_one({"_id": 2})
    r2 = execute_command(coll, {"dbHash": 1})
    assertResult(
        r2,
        expected={"uuids": {"uuid_test": Ne(uuid1)}},
        raw_res=True,
        msg="UUID should change after recreate",
    )
