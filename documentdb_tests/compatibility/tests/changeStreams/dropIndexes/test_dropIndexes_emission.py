"""Verify when dropIndexes change-stream events are emitted.

BSON document-value coverage is not applicable because dropIndexes events
contain index metadata rather than user documents.
"""

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
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Len

pytestmark = [
    pytest.mark.requires(change_streams=True),
    pytest.mark.aggregate,
    pytest.mark.index,
]


def test_dropIndexes_key_pattern_emits_one_event(collection):
    """Drop an index by key pattern and emit its complete specification."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a", name="a_1")
    expected_specification = index_specification(collection, "a_1")

    with open_change_stream(collection, scope="database") as stream:
        drop_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": {"a": 1}},
        )
        events = collect_until_marker(stream, collection)

    matching_events = drop_index_events(
        events,
        collection.database.name,
        collection.name,
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
        msg="dropping by key pattern should emit one complete dropIndexes event",
        raw_res=True,
    )


def test_dropIndexes_array_emits_one_event_per_name(collection):
    """Drop two named indexes in one command and emit one event for each."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.create_index("a", name="a_1")
    collection.create_index("b", name="b_1")
    expected_specifications = {
        name: index_specification(collection, name) for name in ("a_1", "b_1")
    }

    with open_change_stream(collection, scope="database") as stream:
        drop_result = execute_command(
            collection,
            {
                "dropIndexes": collection.name,
                "index": ["a_1", "b_1"],
            },
        )
        events = collect_until_marker(stream, collection)

    matching_events = drop_index_events(
        events,
        collection.database.name,
        collection.name,
    )
    actual_specifications = {
        event["operationDescription"]["indexes"][0]["name"]: event["operationDescription"][
            "indexes"
        ][0]
        for event in matching_events
    }
    observed = {
        "commandSucceeded": (not isinstance(drop_result, Exception) and drop_result.get("ok") == 1),
        "dropEvents": matching_events,
        "specifications": actual_specifications,
    }
    expected = {
        "commandSucceeded": Eq(True),
        "dropEvents": Len(2),
        "dropEvents.0.operationDescription.indexes": Len(1),
        "dropEvents.1.operationDescription.indexes": Len(1),
        "specifications": Eq(expected_specifications),
    }
    assertProperties(
        observed,
        expected,
        msg="an array drop should emit one event per named index",
        raw_res=True,
    )


def test_dropIndexes_star_emits_one_event_per_index(collection):
    """Emit one dropIndexes event for each index removed by dropIndexes('*')."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.create_index("a", name="a_1")
    collection.create_index("b", name="b_1")

    with open_change_stream(collection, scope="database") as stream:
        drop_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": "*"},
        )
        events = collect_until_marker(stream, collection)

    matching_events = drop_index_events(
        events,
        collection.database.name,
        collection.name,
    )
    observed = {
        "commandSucceeded": (not isinstance(drop_result, Exception) and drop_result.get("ok") == 1),
        "dropEvents": matching_events,
        "indexNames": sorted(
            specification["name"]
            for event in matching_events
            for specification in event.get("operationDescription", {}).get("indexes", [])
            if "name" in specification
        ),
    }
    expected = {
        "commandSucceeded": Eq(True),
        "dropEvents": Len(2),
        "dropEvents.0.operationDescription.indexes": Len(1),
        "dropEvents.1.operationDescription.indexes": Len(1),
        "indexNames": Eq(["a_1", "b_1"]),
    }
    assertProperties(
        observed,
        expected,
        msg="dropIndexes('*') should emit one event for each dropped index",
        raw_res=True,
    )


def test_dropIndexes_star_with_only_id_is_noop(collection):
    """Succeed without an event when the collection has only its _id index."""
    collection.insert_one({"_id": 1})

    with open_change_stream(collection, scope="database") as stream:
        drop_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": "*"},
        )
        events = collect_until_marker(stream, collection)

    observed = {
        "commandSucceeded": (not isinstance(drop_result, Exception) and drop_result.get("ok") == 1),
        "dropEvents": drop_index_events(
            events,
            collection.database.name,
            collection.name,
        ),
    }
    expected = {
        "commandSucceeded": Eq(True),
        "dropEvents": Len(0),
    }
    assertProperties(
        observed,
        expected,
        msg="dropIndexes('*') should emit nothing when no secondary index exists",
        raw_res=True,
    )


def test_dropIndexes_id_index_failure_emits_no_event(collection):
    """Reject dropping the _id index and emit no dropIndexes event."""
    collection.insert_one({"_id": 1})

    with open_change_stream(collection, scope="database") as stream:
        drop_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": "_id_"},
        )
        events = collect_until_marker(stream, collection)

    observed = {
        "errorCode": getattr(drop_result, "code", None),
        "dropEvents": drop_index_events(
            events,
            collection.database.name,
            collection.name,
        ),
    }
    expected = {
        "errorCode": Eq(INVALID_OPTIONS_ERROR),
        "dropEvents": Len(0),
    }
    assertProperties(
        observed,
        expected,
        msg="a rejected _id index drop should emit no event",
        raw_res=True,
    )


def test_collection_drop_emits_no_dependent_dropIndexes_event(database_client, collection):
    """Do not emit a dropIndexes event for an index removed with its collection."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a", name="a_1")
    marker_collection = database_client["drop_indexes_marker"]
    marker_collection.insert_one({"setup": True})

    with open_change_stream(collection, scope="database") as stream:
        drop_result = execute_command(
            collection,
            {"drop": collection.name},
        )
        events = collect_until_marker(stream, marker_collection)

    observed = {
        "commandSucceeded": (not isinstance(drop_result, Exception) and drop_result.get("ok") == 1),
        "collectionDropEvents": [
            event
            for event in events
            if event.get("operationType") == "drop"
            and event.get("ns") == {"db": database_client.name, "coll": collection.name}
        ],
        "dropEvents": drop_index_events(
            events,
            database_client.name,
            collection.name,
        ),
    }
    expected = {
        "commandSucceeded": Eq(True),
        "collectionDropEvents": Len(1),
        "dropEvents": Len(0),
    }
    assertProperties(
        observed,
        expected,
        msg="dropping a collection should not emit dependent dropIndexes events",
        raw_res=True,
    )


def test_other_collection_stream_receives_no_dropIndexes_event(collection):
    """Do not deliver a dropIndexes event to a different collection stream."""
    other_collection = collection.database[f"{collection.name}_other"]
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a", name="a_1")
    other_collection.insert_one({"_id": 1})

    with open_change_stream(other_collection, scope="collection") as stream:
        drop_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": "a_1"},
        )
        events = collect_until_marker(stream, other_collection)

    observed = {
        "commandSucceeded": (not isinstance(drop_result, Exception) and drop_result.get("ok") == 1),
        "dropEvents": drop_index_events(
            events,
            collection.database.name,
            collection.name,
        ),
    }
    expected = {
        "commandSucceeded": Eq(True),
        "dropEvents": Len(0),
    }
    assertProperties(
        observed,
        expected,
        msg="a collection stream should not receive another collection's event",
        raw_res=True,
    )


def test_missing_index_failure_emits_no_dropIndexes_event(collection):
    """Return an error and emit no event when the requested index is missing."""
    collection.insert_one({"_id": 1})

    with open_change_stream(collection, scope="database") as stream:
        drop_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": "missing_1"},
        )
        events = collect_until_marker(stream, collection)

    observed = {
        "commandFailed": (isinstance(drop_result, Exception) or drop_result.get("ok") != 1),
        "dropEvents": drop_index_events(
            events,
            collection.database.name,
            collection.name,
        ),
    }
    expected = {
        "commandFailed": Eq(True),
        "dropEvents": Len(0),
    }
    assertProperties(
        observed,
        expected,
        msg="a failed missing-index drop should not emit a dropIndexes event",
        raw_res=True,
    )


def test_showExpandedEvents_omitted_suppresses_dropIndexes_event(collection):
    """Drop the index but emit no event when showExpandedEvents is omitted."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a", name="a_1")

    with open_change_stream(
        collection,
        scope="database",
        show_expanded_events=None,
    ) as stream:
        drop_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": "a_1"},
        )
        events = collect_until_marker(stream, collection)

    listed = execute_command(
        collection,
        {"listIndexes": collection.name, "cursor": {}},
    )
    visible_names = (
        [specification["name"] for specification in listed["cursor"]["firstBatch"]]
        if isinstance(listed, dict)
        else []
    )
    observed = {
        "commandSucceeded": (not isinstance(drop_result, Exception) and drop_result.get("ok") == 1),
        "indexStillVisible": "a_1" in visible_names,
        "dropEvents": drop_index_events(
            events,
            collection.database.name,
            collection.name,
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
        msg="omitting showExpandedEvents should hide the event without blocking the drop",
        raw_res=True,
    )


def test_showExpandedEvents_false_suppresses_dropIndexes_event(collection):
    """Drop the index without returning its event when expanded events are disabled."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a", name="a_1")

    with open_change_stream(
        collection,
        scope="database",
        show_expanded_events=False,
    ) as stream:
        drop_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": "a_1"},
        )
        events = collect_until_marker(stream, collection)

    listed = execute_command(
        collection,
        {"listIndexes": collection.name, "cursor": {}},
    )
    visible_names = (
        [specification["name"] for specification in listed["cursor"]["firstBatch"]]
        if isinstance(listed, dict)
        else []
    )
    observed = {
        "commandSucceeded": (not isinstance(drop_result, Exception) and drop_result.get("ok") == 1),
        "indexStillVisible": "a_1" in visible_names,
        "dropEvents": drop_index_events(
            events,
            collection.database.name,
            collection.name,
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
        msg="showExpandedEvents false should hide the event without blocking the drop",
        raw_res=True,
    )


def test_database_drop_emits_no_dependent_dropIndexes_event(
    engine_client, database_client, collection, register_db_cleanup
):
    """Do not emit a dropIndexes event for an index removed with its database."""
    victim_database_name = f"{database_client.name[:48]}_victim"
    register_db_cleanup(victim_database_name)
    victim_collection = engine_client[victim_database_name]["target"]
    victim_collection.insert_one({"_id": 1, "a": 1})
    victim_collection.create_index("a", name="a_1")

    with open_change_stream(collection, scope="cluster") as stream:
        drop_result = execute_command(
            victim_collection,
            {"dropDatabase": 1},
        )
        events = collect_until_marker(stream, collection)

    observed = {
        "commandSucceeded": (not isinstance(drop_result, Exception) and drop_result.get("ok") == 1),
        "dropEvents": drop_index_events(
            events,
            victim_database_name,
            victim_collection.name,
        ),
    }
    expected = {
        "commandSucceeded": Eq(True),
        "dropEvents": Len(0),
    }
    assertProperties(
        observed,
        expected,
        msg="dropping a database should not emit dependent dropIndexes events",
        raw_res=True,
    )


def test_recreated_index_name_uses_current_specification(collection):
    """Use the current specification and a distinct token for each same-name index."""
    index_name = "same_name"
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.create_index("a", name=index_name)
    first_specification = index_specification(collection, index_name)

    with open_change_stream(collection, scope="database") as stream:
        first_drop_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": index_name},
        )

        collection.create_index([("b", -1)], name=index_name)
        second_specification = index_specification(collection, index_name)
        second_drop_result = execute_command(
            collection,
            {"dropIndexes": collection.name, "index": index_name},
        )
        events = collect_until_marker(stream, collection)

    matching_events = drop_index_events(
        events,
        collection.database.name,
        collection.name,
    )
    tokens = [event.get("_id") for event in matching_events]
    observed = {
        "commandsSucceeded": (
            not isinstance(first_drop_result, Exception)
            and first_drop_result.get("ok") == 1
            and not isinstance(second_drop_result, Exception)
            and second_drop_result.get("ok") == 1
        ),
        "dropEvents": matching_events,
        "eventSpecifications": [
            event.get("operationDescription", {}).get("indexes") for event in matching_events
        ],
        "tokensArePresentAndDistinct": (
            len(tokens) == 2
            and all(token is not None for token in tokens)
            and tokens[0] != tokens[1]
        ),
    }
    expected = {
        "commandsSucceeded": Eq(True),
        "dropEvents": Len(2),
        "eventSpecifications": Eq([[first_specification], [second_specification]]),
        "tokensArePresentAndDistinct": Eq(True),
    }
    assertProperties(
        observed,
        expected,
        msg="recreated index names should use current specifications and distinct tokens",
        raw_res=True,
    )
