"""Record dropIndexes event behavior for each collection variant.

Sharded collections are not applicable because this suite has no sharded
MongoDB target. Regular, capped, view, and time-series collections are covered.
"""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.changeStreams.dropIndexes.utils.drop_indexes import (
    drop_index_events,
    index_specification,
)
from documentdb_tests.compatibility.tests.changeStreams.utils.change_stream import (
    collect_until_marker,
    open_change_stream,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Len
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    TimeseriesCollection,
    ViewCollection,
)

pytestmark = [
    pytest.mark.requires(change_streams=True),
    pytest.mark.aggregate,
    pytest.mark.index,
]


@pytest.mark.parametrize("variant", ["regular", "capped"])
def test_dropIndexes_supported_collection_variant_emits_event(
    database_client,
    collection,
    variant,
):
    """Emit one complete event for an index on a regular or capped collection."""
    if variant == "regular":
        target = collection
    else:
        target = CappedCollection(size=4096).resolve(database_client, collection)

    target.insert_one({"_id": 1, "a": 1})
    target.create_index("a", name="a_1")
    expected_specification = index_specification(target, "a_1")

    with open_change_stream(target, scope="database") as stream:
        drop_result = execute_command(
            target,
            {"dropIndexes": target.name, "index": "a_1"},
        )
        events = collect_until_marker(stream, target)

    matching_events = drop_index_events(
        events,
        target.database.name,
        target.name,
    )
    observed = {
        "commandSucceeded": (not isinstance(drop_result, Exception) and drop_result.get("ok") == 1),
        "dropEvents": matching_events,
    }
    expected = {
        "commandSucceeded": Eq(True),
        "dropEvents": Len(1),
        "dropEvents.0.operationDescription.indexes": Eq([expected_specification]),
    }
    assertProperties(
        observed,
        expected,
        msg=f"{variant} collection should emit one complete dropIndexes event",
        raw_res=True,
    )


def test_dropIndexes_view_fails_and_emits_no_event(database_client, collection):
    """Reject dropIndexes on a view and emit no event."""
    collection.insert_one({"_id": 1, "a": 1})
    view = ViewCollection(options={"pipeline": []}).resolve(
        database_client,
        collection,
    )
    marker_collection = database_client[f"{collection.name}_marker"]
    marker_collection.insert_one({"setup": True})

    with open_change_stream(marker_collection, scope="database") as stream:
        drop_result = execute_command(
            view,
            {"dropIndexes": view.name, "index": "*"},
        )
        events = collect_until_marker(stream, marker_collection)

    observed = {
        "errorCode": getattr(drop_result, "code", None),
        "dropEvents": drop_index_events(
            events,
            database_client.name,
            view.name,
        ),
    }
    expected = {
        "errorCode": Eq(COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR),
        "dropEvents": Len(0),
    }
    assertProperties(
        observed,
        expected,
        msg="dropIndexes on a view should fail without emitting an event",
        raw_res=True,
    )


def test_dropIndexes_timeseries_succeeds_without_event(database_client, collection):
    """Drop a time-series index without emitting a user dropIndexes event."""
    timeseries = TimeseriesCollection(
        timeseries_options={"timeField": "time", "metaField": "meta"},
    ).resolve(database_client, collection)
    timeseries.insert_one(
        {
            "_id": 1,
            "time": datetime.now(timezone.utc),
            "meta": "book",
        }
    )
    timeseries.create_index("meta", name="meta_1")
    marker_collection = database_client[f"{collection.name}_marker"]
    marker_collection.insert_one({"setup": True})

    with open_change_stream(marker_collection, scope="database") as stream:
        drop_result = execute_command(
            timeseries,
            {"dropIndexes": timeseries.name, "index": "meta_1"},
        )
        events = collect_until_marker(stream, marker_collection)

    listed = execute_command(
        timeseries,
        {"listIndexes": timeseries.name, "cursor": {}},
    )
    visible_names = (
        [specification["name"] for specification in listed["cursor"]["firstBatch"]]
        if isinstance(listed, dict)
        else []
    )
    observed = {
        "commandSucceeded": (not isinstance(drop_result, Exception) and drop_result.get("ok") == 1),
        "indexStillVisible": "meta_1" in visible_names,
        "dropEvents": drop_index_events(
            events,
            database_client.name,
            timeseries.name,
        ),
    }
    expected = {
        "commandSucceeded": Eq(True),
        "indexStillVisible": Eq(False),
        "dropEvents": Len(0),
    }
    assertProperties(
        observed,
        expected,
        msg="time-series dropIndexes should remove the index without a user event",
        raw_res=True,
    )
