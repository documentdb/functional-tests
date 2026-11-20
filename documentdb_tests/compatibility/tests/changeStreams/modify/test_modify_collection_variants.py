"""Record collMod Modify behavior for each collection variant.

Regular collections are covered by the index and validation suites. Sharded
collections are not applicable because this suite has no sharded MongoDB
target.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.changeStreams.modify.utils.modify import (
    index_specification,
    modify_events,
)
from documentdb_tests.compatibility.tests.changeStreams.utils.change_stream import (
    collect_until_marker,
    open_change_stream,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Len, NotExists
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    TimeseriesCollection,
    ViewCollection,
)

pytestmark = [
    pytest.mark.requires(change_streams=True),
    pytest.mark.collection_mgmt,
    pytest.mark.aggregate,
]


# Property [Capped Collection]: changing a capped collection's TTL index emits
# one Modify event and reports the capped collection before-state.
@pytest.mark.index
def test_modify_capped_collection_ttl_emits_event(database_client, collection):
    """Emit one TTL Modify event for a capped collection."""
    capped = CappedCollection(size=4096).resolve(
        database_client,
        collection,
    )
    capped.insert_one(
        {
            "_id": 1,
            "createdAt": datetime(2100, 1, 1, tzinfo=timezone.utc),
        }
    )
    capped.create_index(
        "createdAt",
        name="createdAt_1",
        expireAfterSeconds=3600,
    )

    with open_change_stream(capped, scope="database") as stream:
        command_result = execute_command(
            capped,
            {
                "collMod": capped.name,
                "index": {
                    "name": "createdAt_1",
                    "expireAfterSeconds": 7200,
                },
            },
        )
        events = collect_until_marker(stream, capped)
    result = {
        "commandSucceeded": (
            not isinstance(command_result, Exception) and command_result.get("ok") == 1
        ),
        "modifyEvents": modify_events(
            events,
            capped.database.name,
            capped.name,
        ),
        "finalTtl": index_specification(
            capped,
            "createdAt_1",
        )["expireAfterSeconds"],
    }

    assertProperties(
        result,
        {
            "commandSucceeded": Eq(True),
            "modifyEvents": Len(1),
            "modifyEvents.0.operationDescription.index": Eq(
                {
                    "name": "createdAt_1",
                    "expireAfterSeconds": Int64(7200),
                }
            ),
            "modifyEvents.0.stateBeforeChange.collectionOptions.capped": Eq(True),
            "modifyEvents.0.stateBeforeChange.collectionOptions.size": Eq(4096),
            "modifyEvents.0.stateBeforeChange.indexOptions.expireAfterSeconds": Eq(Int64(3600)),
            "finalTtl": Eq(7200),
        },
        msg="a capped collection should emit one complete TTL Modify event",
        raw_res=True,
    )


# Property [View Modification]: changing a view definition emits one Modify
# event containing the requested viewOn and pipeline.
def test_modify_view_reports_requested_definition(collection):
    """Report the requested definition when collMod changes a view."""
    collection.insert_one({"active": True})
    view = ViewCollection(options={"pipeline": []}).resolve(
        collection.database,
        collection,
    )
    requested_pipeline = [{"$match": {"active": True}}]

    with open_change_stream(collection, scope="database") as stream:
        command_result = execute_command(
            view,
            {
                "collMod": view.name,
                "viewOn": collection.name,
                "pipeline": requested_pipeline,
            },
        )
        events = collect_until_marker(stream, collection)
    result = {
        "commandSucceeded": (
            not isinstance(command_result, Exception) and command_result.get("ok") == 1
        ),
        "modifyEvents": modify_events(
            events,
            collection.database.name,
            view.name,
        ),
    }

    assertProperties(
        result,
        {
            "commandSucceeded": Eq(True),
            "modifyEvents": Len(1),
            "modifyEvents.0.operationType": Eq("modify"),
            "modifyEvents.0.ns": Eq(
                {
                    "db": collection.database.name,
                    "coll": view.name,
                }
            ),
            "modifyEvents.0.operationDescription": Eq(
                {
                    "viewOn": collection.name,
                    "pipeline": requested_pipeline,
                }
            ),
            "modifyEvents.0.stateBeforeChange": NotExists(),
        },
        msg="changing a view should emit its requested definition",
        raw_res=True,
    )


# Property [Time-series Collection]: changing a time-series expiration option
# succeeds without emitting a user Modify event.
def test_modify_timeseries_expiration_succeeds_without_event(
    database_client,
    collection,
):
    """Change time-series expiration without a user Modify event."""
    timeseries = TimeseriesCollection(
        timeseries_options={"timeField": "time", "metaField": "meta"},
        create_options={"expireAfterSeconds": 3600},
    ).resolve(database_client, collection)
    timeseries.insert_one(
        {
            "_id": 1,
            "time": datetime.now(timezone.utc),
            "meta": "book",
        }
    )

    with open_change_stream(collection, scope="database") as stream:
        command_result = execute_command(
            timeseries,
            {
                "collMod": timeseries.name,
                "expireAfterSeconds": 7200,
            },
        )
        events = collect_until_marker(stream, collection)

    listed = execute_command(
        timeseries,
        {
            "listCollections": 1,
            "filter": {"name": timeseries.name},
        },
    )
    options = listed["cursor"]["firstBatch"][0]["options"] if isinstance(listed, dict) else {}
    result = {
        "commandSucceeded": (
            not isinstance(command_result, Exception) and command_result.get("ok") == 1
        ),
        "modifyEvents": modify_events(
            events,
            timeseries.database.name,
            timeseries.name,
        ),
        "expiration": options.get("expireAfterSeconds"),
    }

    assertProperties(
        result,
        {
            "commandSucceeded": Eq(True),
            "modifyEvents": Len(0),
            "expiration": Eq(Int64(7200)),
        },
        msg="time-series collMod should update expiration without a user Modify event",
        raw_res=True,
    )
