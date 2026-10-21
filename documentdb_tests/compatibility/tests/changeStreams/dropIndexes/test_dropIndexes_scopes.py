"""Verify dropIndexes event shape at every supported change-stream scope.

Transaction fields are not applicable because MongoDB rejects dropIndexes
inside a multi-document transaction.
"""

from datetime import datetime

import pytest

from documentdb_tests.compatibility.tests.changeStreams.dropIndexes.utils.drop_indexes import (
    collection_uuid,
    drop_index_events,
    index_specification,
)
from documentdb_tests.compatibility.tests.changeStreams.utils.change_stream import (
    collect_until_marker,
    open_change_stream,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import (
    Eq,
    IsType,
    Len,
    NotExists,
)

pytestmark = [
    pytest.mark.requires(change_streams=True),
    pytest.mark.aggregate,
    pytest.mark.index,
]

INDEX_NAME = "a_1_b_-1"


@pytest.mark.parametrize("scope", ["collection", "database", "cluster"])
def test_dropIndexes_event_at_watch_scope(collection, scope):
    """Emit one complete dropIndexes event at the requested watch scope."""
    collection.insert_one({"_id": 1, "a": 1, "b": 2})
    collection.create_index(
        [("a", 1), ("b", -1)],
        name=INDEX_NAME,
        unique=True,
        sparse=True,
    )
    expected_specification = index_specification(collection, INDEX_NAME)
    expected_collection_uuid = collection_uuid(collection)

    with open_change_stream(collection, scope=scope) as stream:
        drop_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": INDEX_NAME},
        )
        events = collect_until_marker(stream, collection)

    matching_events = drop_index_events(
        events,
        collection.database.name,
        collection.name,
    )
    matching_event = matching_events[0] if matching_events else {}
    wall_time = matching_event.get("wallTime")
    observed = {
        "dropSucceeded": (not isinstance(drop_result, Exception) and drop_result.get("ok") == 1),
        "dropEvents": matching_events,
        "listCollectionsUUID": expected_collection_uuid,
        "collectionUuidMatches": (
            expected_collection_uuid is not None
            and matching_event.get("collectionUUID") == expected_collection_uuid
        ),
        "wallTimeIsTimezoneAware": (
            isinstance(wall_time, datetime)
            and wall_time.tzinfo is not None
            and wall_time.utcoffset() is not None
        ),
    }
    expected = {
        "dropSucceeded": Eq(True),
        "dropEvents": Len(1),
        "dropEvents.0.operationType": Eq("dropIndexes"),
        "dropEvents.0.ns": Eq(
            {
                "db": collection.database.name,
                "coll": collection.name,
            }
        ),
        "dropEvents.0.operationDescription.indexes": Eq([expected_specification]),
        "dropEvents.0._id": IsType("object"),
        "dropEvents.0._id._data": IsType("string"),
        "dropEvents.0.clusterTime": IsType("timestamp"),
        "dropEvents.0.collectionUUID": IsType("binData"),
        "dropEvents.0.wallTime": IsType("date"),
        "dropEvents.0.documentKey": NotExists(),
        "dropEvents.0.fullDocument": NotExists(),
        "dropEvents.0.lsid": NotExists(),
        "dropEvents.0.txnNumber": NotExists(),
        "listCollectionsUUID": IsType("binData"),
        "collectionUuidMatches": Eq(True),
        "wallTimeIsTimezoneAware": Eq(True),
    }
    assertProperties(
        observed,
        expected,
        msg=f"{scope} watch should return one complete dropIndexes event",
        raw_res=True,
    )
