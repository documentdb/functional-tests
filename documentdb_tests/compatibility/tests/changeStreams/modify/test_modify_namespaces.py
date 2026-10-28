"""Tests for namespace preservation in collMod Modify events."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.changeStreams.modify.utils.modify import (
    modify_events,
)
from documentdb_tests.compatibility.tests.changeStreams.utils.change_stream import (
    collect_until_marker,
    open_change_stream,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq, Len

pytestmark = [
    pytest.mark.requires(change_streams=True),
    pytest.mark.collection_mgmt,
    pytest.mark.aggregate,
]


# Property [Namespace Preservation]: Modify events retain compatible long and
# special database and collection names.
@pytest.mark.index
@pytest.mark.parametrize(
    "namespace_kind",
    [
        "long_collection",
        "special_collection",
        "long_database",
        "special_database",
    ],
)
def test_modify_event_preserves_namespace(collection, register_db_cleanup, namespace_kind):
    """Preserve long and special database and collection names in the event."""
    target_database = collection.database
    collection_name = collection.name

    if namespace_kind == "long_collection":
        collection_name = (collection.name + "_" + ("c" * 64))[:64]
    elif namespace_kind == "special_collection":
        collection_name = f"{collection.name}.éditions"
    elif namespace_kind == "long_database":
        unique_suffix = target_database.name[-16:]
        database_name = ("d" * (62 - len(unique_suffix))) + "_" + unique_suffix
        register_db_cleanup(database_name)
        target_database = target_database.client[database_name]
    else:
        database_name = f"{target_database.name[:48]}-é"
        register_db_cleanup(database_name)
        target_database = target_database.client[database_name]

    target_database.create_collection(collection_name)
    target = target_database[collection_name]
    target.create_index(
        "createdAt",
        name="createdAt_1",
        expireAfterSeconds=3600,
    )

    with open_change_stream(target, scope="database") as stream:
        command_result = execute_command(
            target,
            {
                "collMod": target.name,
                "index": {
                    "name": "createdAt_1",
                    "expireAfterSeconds": 7200,
                },
            },
        )
        events = collect_until_marker(stream, target)
    result = {
        "commandSucceeded": (
            not isinstance(command_result, Exception) and command_result.get("ok") == 1
        ),
        "modifyEvents": modify_events(
            events,
            target.database.name,
            target.name,
        ),
    }

    assertProperties(
        result,
        {
            "commandSucceeded": Eq(True),
            "modifyEvents": Len(1),
            "modifyEvents.0.ns": Eq(
                {
                    "db": target.database.name,
                    "coll": target.name,
                }
            ),
        },
        msg=f"a Modify event should preserve the {namespace_kind} namespace",
        raw_res=True,
    )
