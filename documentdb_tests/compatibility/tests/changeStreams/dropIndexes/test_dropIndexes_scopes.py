"""Verify dropIndexes events at every supported change-stream scope."""

import pytest

from documentdb_tests.compatibility.tests.changeStreams.dropIndexes.utils.drop_indexes import (
    collect_until_marker,
    drop_index_events,
    index_specification,
    open_change_stream,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Exists, Len

pytestmark = [
    pytest.mark.requires(change_streams=True),
    pytest.mark.aggregate,
    pytest.mark.index,
]

INDEX_NAME = "a_1_b_-1"


@pytest.mark.parametrize("scope", ["collection", "database", "cluster"])
def test_dropIndexes_event_at_watch_scope(collection, scope):
    """Emit one complete, non-invalidating dropIndexes event at the watch scope."""
    collection.insert_one({"_id": 1, "a": 1, "b": 2})
    collection.create_index(
        [("a", 1), ("b", -1)],
        name=INDEX_NAME,
        unique=True,
        sparse=True,
    )
    expected_specification = index_specification(collection, INDEX_NAME)

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
    observed = {
        "dropSucceeded": (not isinstance(drop_result, Exception) and drop_result.get("ok") == 1),
        "dropEvents": matching_events,
        "invalidateEvents": [
            event for event in events if event.get("operationType") == "invalidate"
        ],
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
        "dropEvents.0._id": Exists(),
        "dropEvents.0.clusterTime": Exists(),
        "invalidateEvents": Len(0),
    }
    assertProperties(
        observed,
        expected,
        msg=f"{scope} watch should return one complete dropIndexes event",
        raw_res=True,
    )
