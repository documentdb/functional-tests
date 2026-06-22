"""Tests for validate command on different collection types.

Validates behavior on regular, capped, view, timeseries, and clustered collections.
"""

from __future__ import annotations

from datetime import datetime, timezone

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR
from documentdb_tests.framework.executor import execute_command


def test_validate_capped_collection(database_client, collection):
    """Test validate on a capped collection succeeds."""
    coll_name = f"{collection.name}_capped"
    database_client.create_collection(coll_name, capped=True, size=1_048_576)
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1, "x": 1})
    result = execute_command(coll, {"validate": coll.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True},
        msg="validate should succeed on a capped collection",
    )


def test_validate_view_rejected(database_client, collection):
    """Test validate on a view returns an error."""
    source_name = f"{collection.name}_view_source"
    view_name = f"{collection.name}_view"
    database_client.create_collection(source_name)
    database_client[source_name].insert_one({"_id": 1})
    database_client.command("create", view_name, viewOn=source_name, pipeline=[])
    coll = database_client[view_name]
    result = execute_command(coll, {"validate": coll.name})
    assertFailureCode(
        result,
        COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="validate should reject views",
    )


def test_validate_timeseries_collection(database_client, collection):
    """Test validate on a time series collection succeeds."""
    coll_name = f"{collection.name}_timeseries"
    database_client.create_collection(
        coll_name,
        timeseries={"timeField": "ts", "metaField": "meta"},
    )
    coll = database_client[coll_name]
    coll.insert_one({"ts": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "a", "v": 1})
    result = execute_command(coll, {"validate": coll.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="validate should succeed on a timeseries collection",
    )


def test_validate_clustered_collection(database_client, collection):
    """Test validate on a clustered collection succeeds."""
    coll_name = f"{collection.name}_clustered"
    database_client.command(
        "create",
        coll_name,
        clusteredIndex={"key": {"_id": 1}, "unique": True},
    )
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1, "x": 1})
    result = execute_command(coll, {"validate": coll.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="validate should succeed on a clustered collection",
    )
