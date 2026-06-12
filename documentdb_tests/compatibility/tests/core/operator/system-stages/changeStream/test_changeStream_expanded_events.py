"""Tests for $changeStream showExpandedEvents operationType gating."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest
from utils.changeStream_common import change_stream_command, get_more_command

from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, NotContains
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class DdlOperation:
    """A DDL/metadata operation observed through a change stream.

    Attributes:
        operation_type: The ``operationType`` the resulting event carries, used
            to find the event among the drained events
        command: Builds the command document from the fixture collection
        scope: The change-stream scope the operation must be observed at
            (``collection`` or ``database``)
        admin: Routes ``command`` through ``execute_admin_command`` rather than
            ``execute_command`` (e.g. rename)
        setup: Builds a precondition command run before the stream opens, e.g.
            creating an index so it can later be dropped (None when not needed)
    """

    operation_type: str
    command: Callable[[Any], dict[str, Any]]
    scope: str = "collection"
    admin: bool = False
    setup: Callable[[Any], dict[str, Any]] | None = None


def _create_index_command(collection) -> dict[str, Any]:
    return {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]}


def _create_index() -> DdlOperation:
    """Create an index; emits a createIndexes event."""
    return DdlOperation("createIndexes", _create_index_command)


def _drop_index() -> DdlOperation:
    """Drop an index (created during setup); emits a dropIndexes event."""
    return DdlOperation(
        "dropIndexes",
        lambda c: {"dropIndexes": c.name, "index": "a_1"},
        setup=_create_index_command,
    )


def _coll_mod() -> DdlOperation:
    """Modify collection options; emits a modify event."""
    return DdlOperation("modify", lambda c: {"collMod": c.name, "validationLevel": "moderate"})


def _create() -> DdlOperation:
    """Create a sibling collection; emits a create event on a database-scoped stream."""
    return DdlOperation("create", lambda c: {"create": f"{c.name}_ddl"}, scope="database")


def _drop() -> DdlOperation:
    """Drop the collection; emits a drop event."""
    return DdlOperation("drop", lambda c: {"drop": c.name})


def _rename() -> DdlOperation:
    """Rename the collection; emits a rename event."""
    return DdlOperation(
        "rename",
        lambda c: {
            "renameCollection": f"{c.database.name}.{c.name}",
            "to": f"{c.database.name}.{c.name}_renamed",
        },
        admin=True,
    )


@dataclass(frozen=True)
class ChangeStreamGatingTestCase(BaseTestCase):
    """Test case for $changeStream showExpandedEvents operationType gating.

    Drives an open-DDL-drain sequence: the stream is opened with ``pipeline``
    (the full ``[{"$changeStream": ...}]`` pipeline) at the scope ``ddl``
    requires, the DDL operation is performed, and the drained command result is
    checked against the inherited ``expected`` property map.

    Attributes:
        pipeline: The full ``[{"$changeStream": ...}]`` pipeline to open with,
            at the scope ``ddl`` requires (required)
        ddl: The DDL operation to perform, see ``DdlOperation`` (required)
        expected: A property-check map over the raw getMore result; for a
            gating case it asserts the cursor batch ``Contains`` (shown) or
            ``NotContains`` (suppressed) an event with the ddl's operationType
            (inherited from ``BaseTestCase``)
    """

    pipeline: list[dict[str, Any]] | None = None
    ddl: DdlOperation | None = None

    def __post_init__(self):
        super().__post_init__()
        if self.pipeline is None:
            raise ValueError(f"ChangeStreamGatingTestCase '{self.id}' must set pipeline")
        if self.ddl is None:
            raise ValueError(f"ChangeStreamGatingTestCase '{self.id}' must set ddl")


# Property [Expanded Event Gating]: showExpandedEvents true surfaces the
# expanded DDL/index events that showExpandedEvents false or omission suppresses.
CHANGESTREAM_EXPANDED_EVENT_GATING_TESTS: list[ChangeStreamGatingTestCase] = [
    ChangeStreamGatingTestCase(
        "create_index_shown_when_true",
        pipeline=[{"$changeStream": {"showExpandedEvents": True}}],
        ddl=_create_index(),
        expected={"cursor": {"nextBatch": Contains("operationType", "createIndexes")}},
        msg="$changeStream should emit a createIndexes event when showExpandedEvents is true",
    ),
    ChangeStreamGatingTestCase(
        "create_index_suppressed_when_false",
        pipeline=[{"$changeStream": {"showExpandedEvents": False}}],
        ddl=_create_index(),
        expected={"cursor": {"nextBatch": NotContains("operationType", "createIndexes")}},
        msg=(
            "$changeStream should suppress the createIndexes event when"
            " showExpandedEvents is false"
        ),
    ),
    ChangeStreamGatingTestCase(
        "create_index_suppressed_when_omitted",
        pipeline=[{"$changeStream": {}}],
        ddl=_create_index(),
        expected={"cursor": {"nextBatch": NotContains("operationType", "createIndexes")}},
        msg=(
            "$changeStream should suppress the createIndexes event when"
            " showExpandedEvents is omitted"
        ),
    ),
    ChangeStreamGatingTestCase(
        "coll_mod_shown_when_true",
        pipeline=[{"$changeStream": {"showExpandedEvents": True}}],
        ddl=_coll_mod(),
        expected={"cursor": {"nextBatch": Contains("operationType", "modify")}},
        msg="$changeStream should emit a modify event when showExpandedEvents is true",
    ),
    ChangeStreamGatingTestCase(
        "coll_mod_suppressed_when_false",
        pipeline=[{"$changeStream": {"showExpandedEvents": False}}],
        ddl=_coll_mod(),
        expected={"cursor": {"nextBatch": NotContains("operationType", "modify")}},
        msg="$changeStream should suppress the modify event when showExpandedEvents is false",
    ),
    ChangeStreamGatingTestCase(
        "drop_index_shown_when_true",
        pipeline=[{"$changeStream": {"showExpandedEvents": True}}],
        ddl=_drop_index(),
        expected={"cursor": {"nextBatch": Contains("operationType", "dropIndexes")}},
        msg="$changeStream should emit a dropIndexes event when showExpandedEvents is true",
    ),
    ChangeStreamGatingTestCase(
        "drop_index_suppressed_when_false",
        pipeline=[{"$changeStream": {"showExpandedEvents": False}}],
        ddl=_drop_index(),
        expected={"cursor": {"nextBatch": NotContains("operationType", "dropIndexes")}},
        msg="$changeStream should suppress the dropIndexes event when showExpandedEvents is false",
    ),
    ChangeStreamGatingTestCase(
        "create_shown_when_true",
        pipeline=[{"$changeStream": {"showExpandedEvents": True}}],
        ddl=_create(),
        expected={"cursor": {"nextBatch": Contains("operationType", "create")}},
        msg="$changeStream should emit a create event when showExpandedEvents is true",
    ),
    ChangeStreamGatingTestCase(
        "create_suppressed_when_false",
        pipeline=[{"$changeStream": {"showExpandedEvents": False}}],
        ddl=_create(),
        expected={"cursor": {"nextBatch": NotContains("operationType", "create")}},
        msg="$changeStream should suppress the create event when showExpandedEvents is false",
    ),
]

# Property [DDL Event Emission Regardless Of showExpandedEvents]: drop and
# rename events are emitted whether showExpandedEvents is true or false.
CHANGESTREAM_DDL_ALWAYS_EMITTED_TESTS: list[ChangeStreamGatingTestCase] = [
    ChangeStreamGatingTestCase(
        "drop_emitted_true",
        pipeline=[{"$changeStream": {"showExpandedEvents": True}}],
        ddl=_drop(),
        expected={"cursor": {"nextBatch": Contains("operationType", "drop")}},
        msg="$changeStream should emit a drop event when showExpandedEvents is true",
    ),
    ChangeStreamGatingTestCase(
        "drop_emitted_false",
        pipeline=[{"$changeStream": {"showExpandedEvents": False}}],
        ddl=_drop(),
        expected={"cursor": {"nextBatch": Contains("operationType", "drop")}},
        msg="$changeStream should emit a drop event when showExpandedEvents is false",
    ),
    ChangeStreamGatingTestCase(
        "rename_emitted_true",
        pipeline=[{"$changeStream": {"showExpandedEvents": True}}],
        ddl=_rename(),
        expected={"cursor": {"nextBatch": Contains("operationType", "rename")}},
        msg="$changeStream should emit a rename event when showExpandedEvents is true",
    ),
    ChangeStreamGatingTestCase(
        "rename_emitted_false",
        pipeline=[{"$changeStream": {"showExpandedEvents": False}}],
        ddl=_rename(),
        expected={"cursor": {"nextBatch": Contains("operationType", "rename")}},
        msg="$changeStream should emit a rename event when showExpandedEvents is false",
    ),
]

CHANGESTREAM_EXPANDED_EVENT_TESTS = (
    CHANGESTREAM_EXPANDED_EVENT_GATING_TESTS + CHANGESTREAM_DDL_ALWAYS_EMITTED_TESTS
)


def _emit_ddl_result(collection, database_client, test_case: ChangeStreamGatingTestCase) -> Any:
    """Open a stream, perform the DDL operation, and return the raw getMore result.

    For a suppression case a marker insert follows the DDL so the getMore
    returns an event instead of blocking until maxTimeMS.
    """
    ddl = test_case.ddl
    assert ddl is not None  # guaranteed by __post_init__
    suppression = isinstance(test_case.expected["cursor"]["nextBatch"], NotContains)
    database_scope = ddl.scope == "database"

    if not database_scope:
        collection.insert_one({"_id": 1})
        if ddl.setup is not None:
            execute_command(collection, ddl.setup(collection))

    open_kwargs = {"aggregate": 1} if database_scope else {}
    opened = execute_command(
        collection, change_stream_command(collection, pipeline=test_case.pipeline, **open_kwargs)
    )

    run = execute_admin_command if ddl.admin else execute_command
    run(collection, ddl.command(collection))

    if suppression:
        if database_scope:
            database_client[f"{collection.name}_ddl"].insert_one({"_id": 1})
        else:
            collection.insert_one({"_id": 99})

    getmore_kwargs = {"name": "$cmd.aggregate"} if database_scope else {}
    return execute_command(
        collection, get_more_command(collection, opened["cursor"]["id"], **getmore_kwargs)
    )


@pytest.mark.replica_set
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_EXPANDED_EVENT_TESTS))
def test_changeStream_showExpandedEvents_event_gating(
    collection, database_client, test_case: ChangeStreamGatingTestCase
):
    """Test $changeStream showExpandedEvents gating of expanded DDL/index events."""
    result = _emit_ddl_result(collection, database_client, test_case)
    assertProperties(result, test_case.expected, msg=test_case.msg, raw_res=True)
