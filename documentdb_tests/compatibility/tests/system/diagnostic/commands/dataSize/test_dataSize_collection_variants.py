"""Tests for dataSize command with different collection types."""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.admin


def test_dataSize_regular_collection(collection):
    """Test dataSize on regular collection succeeds."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Regular collection should succeed")


def test_dataSize_capped_collection(database_client):
    """Test dataSize on capped collection succeeds."""
    database_client.create_collection("capped_ds", capped=True, size=4096)
    database_client["capped_ds"].insert_one({"_id": 1})
    ns = f"{database_client.name}.capped_ds"
    coll = database_client["capped_ds"]
    result = execute_command(coll, {"dataSize": ns})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Capped collection should succeed")


def test_dataSize_view(database_client):
    """Test dataSize on a view returns error."""
    database_client.create_collection("base_ds")
    database_client.command("create", "ds_view", viewOn="base_ds", pipeline=[])
    ns = f"{database_client.name}.ds_view"
    coll = database_client["ds_view"]
    result = execute_command(coll, {"dataSize": ns})
    assertFailureCode(result, COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR, msg="View should error")
