"""Tests for the $currentOp aggregation pipeline stage against live operation state."""

from __future__ import annotations

import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, Gte, NotExists


@dataclass(frozen=True)
class LiveState:
    """Default. No additional concurrent operation is in flight."""

    @contextmanager
    def hold(self, collection) -> Iterator[None]:
        """Establish the concurrent state, run the body, then tear it down."""
        yield

    @staticmethod
    def _wait_for_op(collection, op: str, timeout_seconds: float = 10.0) -> None:
        """Poll currentOp until an operation of the given op type is in flight.

        Returns as soon as the op is observable so the caller can yield while it
        is still running. Raises AssertionError if the op never appears within
        timeout_seconds, so the failure is reported at its root cause rather
        than as a confusing downstream assertion failure.
        """
        deadline = time.monotonic() + timeout_seconds
        poll_interval_seconds = 0.05
        while time.monotonic() < deadline:
            ops = collection.database.client.admin.command(
                {"currentOp": True, "op": op, "$all": True}
            )
            if ops["inprog"]:
                return
            time.sleep(poll_interval_seconds)
        raise AssertionError(
            f"operation {op!r} did not appear in currentOp within {timeout_seconds}s"
        )


@dataclass(frozen=True)
class IdleCursor(LiveState):
    """An idle find cursor left open with documents still unfetched."""

    @contextmanager
    def hold(self, collection) -> Iterator[None]:
        collection.insert_many([{"x": i} for i in range(5)])
        cursor_id = execute_command(collection, {"find": collection.name, "batchSize": 2})[
            "cursor"
        ]["id"]
        try:
            yield
        finally:
            execute_command(collection, {"killCursors": collection.name, "cursors": [cursor_id]})


@dataclass(frozen=True)
class LockHoldingTransaction(LiveState):
    """An open multi-document transaction holding a write lock."""

    @contextmanager
    def hold(self, collection) -> Iterator[None]:
        collection.insert_one({"_id": 1, "v": 0})
        session = collection.database.client.start_session()
        session.start_transaction()
        try:
            collection.update_one({"_id": 1}, {"$set": {"v": 1}}, session=session)
            yield
        finally:
            session.abort_transaction()
            session.end_session()


@dataclass(frozen=True)
class ActiveGetMore(LiveState):
    """An active getMore: a find cursor iterated with a per-document sleep so the
    getMore is still executing when $currentOp observes it."""

    @contextmanager
    def hold(self, collection) -> Iterator[None]:
        collection.insert_many([{"v": i} for i in range(10)])

        def run() -> None:
            try:
                cursor = collection.find({"$where": "sleep(200) || true"}, batch_size=1)
                for _ in cursor:
                    pass
            except Exception:
                pass

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        try:
            # Wait until the find has issued its first getMore so $currentOp can
            # observe it, rather than relying on a fixed delay.
            self._wait_for_op(collection, "getmore")
            yield
        finally:
            thread.join(timeout=10)


@dataclass(frozen=True)
class InFlightLargeCommand(LiveState):
    """An in-flight find whose command document exceeds 1 KB, held briefly by a
    single-document $where sleep so $currentOp observes its command.

    When comment is set it is added to the find command, which is carried out of
    a truncated command as a sibling key.
    """

    comment: str | None = None

    @contextmanager
    def hold(self, collection) -> Iterator[None]:
        collection.insert_one({"_id": 1, "v": 0})
        # Inflate the command well past 1 KB without scanning more documents or
        # lengthening the sleep: the predicate runs once on the single document.
        large_predicate = "sleep(1800) || true" + (" || true" * 300)
        comment = self.comment

        def run() -> None:
            try:
                kwargs: dict = {}
                if comment is not None:
                    kwargs["comment"] = comment
                list(collection.find({"$where": large_predicate}, **kwargs))
            except Exception:
                pass

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        try:
            # Wait until the in-flight find command is observable to $currentOp
            # instead of relying on a fixed delay.
            self._wait_for_op(collection, "query")
            yield
        finally:
            thread.join(timeout=10)


@dataclass(frozen=True)
class CurrentOpLiveCase(StageTestCase):
    """Test case for a $currentOp pipeline observed against live operation state."""

    live_state: LiveState = field(default_factory=LiveState)


# Property [idleConnections Flag]: idleConnections:true reports inactive
# connections as op documents with active:false, while idleConnections:false
# suppresses every inactive document.
CURRENTOP_IDLE_CONNECTIONS_TESTS: list[CurrentOpLiveCase] = [
    CurrentOpLiveCase(
        "idle_connections_true_reports_inactive",
        pipeline=[
            {"$currentOp": {"idleConnections": True}},
            {"$match": {"type": "op", "active": False}},
            {"$count": "n"},
        ],
        expected={"n": Gte(1)},
        msg="$currentOp should report inactive operations when idleConnections is true",
    ),
    CurrentOpLiveCase(
        "idle_connections_false_suppresses_inactive",
        pipeline=[
            {"$currentOp": {"idleConnections": False}},
            {"$match": {"active": False}},
            {"$count": "n"},
        ],
        expected=[],
        msg="$currentOp should suppress inactive operations when idleConnections is false",
        marks=(pytest.mark.no_parallel,),
    ),
]

# Property [idleCursors Flag]: idleCursors:true reports idle cursors as type
# "idleCursor" documents, while the default or false emits none.
CURRENTOP_IDLE_CURSORS_TESTS: list[CurrentOpLiveCase] = [
    CurrentOpLiveCase(
        "idle_cursors_true_reports_cursor",
        live_state=IdleCursor(),
        pipeline=[
            {"$currentOp": {"idleCursors": True, "idleConnections": False}},
            {"$match": {"type": "idleCursor"}},
            {"$count": "n"},
        ],
        expected={"n": Gte(1)},
        msg="$currentOp should report idle cursors when idleCursors is true",
    ),
    CurrentOpLiveCase(
        "idle_cursors_false_suppresses_cursor",
        live_state=IdleCursor(),
        pipeline=[
            {"$currentOp": {"idleCursors": False, "idleConnections": False}},
            {"$match": {"type": "idleCursor"}},
            {"$count": "n"},
        ],
        expected=[],
        msg="$currentOp should emit no idle cursors when idleCursors is false",
        marks=(pytest.mark.no_parallel,),
    ),
]

# Property [idleSessions Flag]: an inactive lock-holding session is reported as
# a type "idleSession" document when idleSessions is true or omitted (the
# documented default is true), and suppressed when it is false.
CURRENTOP_IDLE_SESSIONS_TESTS: list[CurrentOpLiveCase] = [
    CurrentOpLiveCase(
        "idle_sessions_true_reports_session",
        live_state=LockHoldingTransaction(),
        pipeline=[
            {"$currentOp": {"idleSessions": True, "idleConnections": False}},
            {"$match": {"type": "idleSession"}},
            {"$count": "n"},
        ],
        expected={"n": Gte(1)},
        msg="$currentOp should report a lock-holding session when idleSessions is true",
        marks=(pytest.mark.requires(transactions=True),),
    ),
    CurrentOpLiveCase(
        "idle_sessions_default_reports_session",
        live_state=LockHoldingTransaction(),
        pipeline=[
            {"$currentOp": {"idleConnections": False}},
            {"$match": {"type": "idleSession"}},
            {"$count": "n"},
        ],
        expected={"n": Gte(1)},
        msg="$currentOp should report a lock-holding session when idleSessions is omitted",
        marks=(pytest.mark.requires(transactions=True),),
    ),
    CurrentOpLiveCase(
        "idle_sessions_false_suppresses_session",
        live_state=LockHoldingTransaction(),
        pipeline=[
            {"$currentOp": {"idleSessions": False, "idleConnections": False}},
            {"$match": {"type": "idleSession"}},
            {"$count": "n"},
        ],
        expected=[],
        msg="$currentOp should suppress a lock-holding session when idleSessions is false",
        marks=(pytest.mark.requires(transactions=True), pytest.mark.no_parallel),
    ),
]

# Property [idleSessions Without Transaction]: no idleSession documents appear
# when no lock-holding transaction is open.
CURRENTOP_IDLE_SESSIONS_ABSENT_TESTS: list[CurrentOpLiveCase] = [
    CurrentOpLiveCase(
        "idle_sessions_absent_without_transaction",
        pipeline=[
            {"$currentOp": {"idleSessions": True, "idleConnections": False}},
            {"$match": {"type": "idleSession"}},
            {"$count": "n"},
        ],
        expected=[],
        msg="$currentOp should report no idle sessions without an open lock-holding transaction",
        marks=(pytest.mark.no_parallel,),
    ),
]

# Property [Emitted Document Type Set]: every emitted item has a type that is
# one of "op", "idleSession", or "idleCursor".
CURRENTOP_EMITTED_TYPE_TESTS: list[CurrentOpLiveCase] = [
    CurrentOpLiveCase(
        "emitted_document_types",
        live_state=LockHoldingTransaction(),
        pipeline=[
            {"$currentOp": {"idleConnections": True, "idleCursors": True, "idleSessions": True}},
            {"$match": {"type": {"$nin": ["op", "idleSession", "idleCursor"]}}},
            {"$count": "n"},
        ],
        expected=[],
        msg="$currentOp should emit only documents whose type is op, idleSession, or idleCursor",
        marks=(pytest.mark.requires(transactions=True), pytest.mark.no_parallel),
    ),
]

# Property [Emitted Document Shard Field]: neither shard nor client_s appears on
# any emitted document on a non-sharded deployment.
CURRENTOP_EMITTED_SHARD_TESTS: list[CurrentOpLiveCase] = [
    CurrentOpLiveCase(
        "emitted_document_no_shard_fields",
        pipeline=[
            {"$currentOp": {"idleConnections": True}},
            {"$match": {"$or": [{"shard": {"$exists": True}}, {"client_s": {"$exists": True}}]}},
            {"$count": "n"},
        ],
        expected=[],
        msg="$currentOp should omit shard and client_s fields on a non-sharded deployment",
        marks=(pytest.mark.no_parallel,),
    ),
]

# Property [idleCursor Document Fields]: an idleCursor document carries the
# cursor sub-document but omits op, cursor.operationUsingCursorId,
# cursor.planSummary, transaction, client, and secs_running.
CURRENTOP_IDLE_CURSOR_FIELD_TESTS: list[CurrentOpLiveCase] = [
    CurrentOpLiveCase(
        "idle_cursor_document_fields",
        live_state=IdleCursor(),
        pipeline=[
            {"$currentOp": {"idleCursors": True, "idleConnections": False}},
            {"$match": {"type": "idleCursor"}},
            {"$limit": 1},
        ],
        expected={
            "type": Eq("idleCursor"),
            "cursor": Exists(),
            "op": NotExists(),
            "cursor.operationUsingCursorId": NotExists(),
            "cursor.planSummary": NotExists(),
            "transaction": NotExists(),
            "client": NotExists(),
            "secs_running": NotExists(),
        },
        msg="$currentOp idleCursor documents should omit the active-op and client-op fields",
    ),
]

# Property [idleSession Document Fields]: the idleSession document of an open
# lock-holding transaction carries the transaction sub-document and lsid but
# omits op and secs_running.
CURRENTOP_IDLE_SESSION_FIELD_TESTS: list[CurrentOpLiveCase] = [
    CurrentOpLiveCase(
        "idle_session_document_fields",
        live_state=LockHoldingTransaction(),
        pipeline=[
            {"$currentOp": {"idleSessions": True, "idleConnections": True}},
            {"$match": {"type": "idleSession"}},
            {"$limit": 1},
        ],
        expected={
            "type": Eq("idleSession"),
            "transaction": Exists(),
            "lsid": Exists(),
            "op": NotExists(),
            "secs_running": NotExists(),
        },
        msg="$currentOp idleSession documents should carry the transaction sub-document and lsid",
        marks=(pytest.mark.requires(transactions=True),),
    ),
]

# Property [Inactive op Document Fields]: an inactive type "op" document omits
# the running-time fields (secs_running, microsecs_running) and the transaction
# sub-document.
CURRENTOP_INACTIVE_OP_FIELD_TESTS: list[CurrentOpLiveCase] = [
    CurrentOpLiveCase(
        "inactive_op_document_fields",
        pipeline=[
            {"$currentOp": {"idleConnections": True}},
            {"$match": {"type": "op", "active": False}},
            {"$limit": 1},
        ],
        expected={
            "type": Eq("op"),
            "active": Eq(False),
            "secs_running": NotExists(),
            "microsecs_running": NotExists(),
            "transaction": NotExists(),
        },
        msg="$currentOp inactive op documents should omit running-time and transaction fields",
    ),
]

# Property [Active getMore Document Fields]: an active getMore is a type "op"
# document with op "getmore" that carries the running-time fields, the cursor
# sub-document, and cursor.operationUsingCursorId, while omitting the
# transaction sub-document.
CURRENTOP_ACTIVE_GETMORE_FIELD_TESTS: list[CurrentOpLiveCase] = [
    CurrentOpLiveCase(
        "active_getmore_document_fields",
        live_state=ActiveGetMore(),
        pipeline=[
            {"$currentOp": {"allUsers": True, "idleConnections": True}},
            {"$match": {"op": "getmore"}},
            {"$limit": 1},
        ],
        expected={
            "type": Eq("op"),
            "op": Eq("getmore"),
            "active": Eq(True),
            "secs_running": Exists(),
            "microsecs_running": Exists(),
            "cursor": Exists(),
            "cursor.operationUsingCursorId": Exists(),
            "transaction": NotExists(),
        },
        msg="$currentOp active getMore documents should carry running-time and cursor fields",
    ),
]

# Property [Command Not Truncated]: the command document is emitted in full
# (no $truncated key) when truncateOps is omitted or false regardless of the
# command size, and when truncateOps is true but the command is at or under the
# size threshold.
CURRENTOP_FULL_COMMAND_TESTS: list[CurrentOpLiveCase] = [
    CurrentOpLiveCase(
        "command_full_truncateOps_omitted_large",
        live_state=InFlightLargeCommand(),
        pipeline=[
            {"$currentOp": {"allUsers": True, "idleConnections": True}},
            {"$match": {"command.find": {"$exists": True}}},
            {"$limit": 1},
        ],
        expected={
            "command.find": Exists(),
            "command.$truncated": NotExists(),
        },
        msg="$currentOp should emit a large command in full when truncateOps is omitted",
    ),
    CurrentOpLiveCase(
        "command_full_truncateOps_false_large",
        live_state=InFlightLargeCommand(),
        pipeline=[
            {"$currentOp": {"truncateOps": False, "allUsers": True, "idleConnections": True}},
            {"$match": {"command.find": {"$exists": True}}},
            {"$limit": 1},
        ],
        expected={
            "command.find": Exists(),
            "command.$truncated": NotExists(),
        },
        msg="$currentOp should emit a large command in full when truncateOps is false",
    ),
]

# Property [Command Truncated]: with truncateOps true and a command larger than
# the size threshold, the command document is replaced by a single $truncated
# string key.
CURRENTOP_TRUNCATED_COMMAND_TESTS: list[CurrentOpLiveCase] = [
    CurrentOpLiveCase(
        "command_truncated_large",
        live_state=InFlightLargeCommand(),
        pipeline=[
            {"$currentOp": {"truncateOps": True, "allUsers": True, "idleConnections": True}},
            {"$match": {"command.$truncated": {"$exists": True}}},
            {"$limit": 1},
        ],
        expected={
            "command.$truncated": Exists(),
            "command.find": NotExists(),
            "command.comment": NotExists(),
        },
        msg="$currentOp should replace a large command with a single $truncated key",
        marks=(pytest.mark.no_parallel,),
    ),
]

# Property [Truncated Command Comment Sibling]: with truncateOps true and a
# command larger than the size threshold, a comment is carried out of the
# truncated command as a sibling key alongside $truncated.
CURRENTOP_TRUNCATED_COMMENT_TESTS: list[CurrentOpLiveCase] = [
    CurrentOpLiveCase(
        "command_truncated_comment_sibling",
        live_state=InFlightLargeCommand(comment="currentOp_truncation_marker"),
        pipeline=[
            {"$currentOp": {"truncateOps": True, "allUsers": True, "idleConnections": True}},
            {"$match": {"command.$truncated": {"$exists": True}}},
            {"$limit": 1},
        ],
        expected={
            "command.$truncated": Exists(),
            "command.comment": Eq("currentOp_truncation_marker"),
        },
        msg="$currentOp should carry the comment as a sibling key of a truncated command",
        marks=(pytest.mark.no_parallel,),
    ),
]

CURRENTOP_LIVE_TESTS: list[CurrentOpLiveCase] = (
    CURRENTOP_IDLE_CONNECTIONS_TESTS
    + CURRENTOP_IDLE_CURSORS_TESTS
    + CURRENTOP_IDLE_SESSIONS_TESTS
    + CURRENTOP_IDLE_SESSIONS_ABSENT_TESTS
    + CURRENTOP_EMITTED_TYPE_TESTS
    + CURRENTOP_EMITTED_SHARD_TESTS
    + CURRENTOP_IDLE_CURSOR_FIELD_TESTS
    + CURRENTOP_IDLE_SESSION_FIELD_TESTS
    + CURRENTOP_INACTIVE_OP_FIELD_TESTS
    + CURRENTOP_ACTIVE_GETMORE_FIELD_TESTS
    + CURRENTOP_FULL_COMMAND_TESTS
    + CURRENTOP_TRUNCATED_COMMAND_TESTS
    + CURRENTOP_TRUNCATED_COMMENT_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CURRENTOP_LIVE_TESTS))
def test_currentOp_live_state(collection, test_case: CurrentOpLiveCase):
    """Test $currentOp reporting against an in-flight operation or session."""
    with test_case.live_state.hold(collection):
        result = execute_admin_command(
            collection,
            {"aggregate": 1, "pipeline": test_case.pipeline, "cursor": {}},
        )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)
