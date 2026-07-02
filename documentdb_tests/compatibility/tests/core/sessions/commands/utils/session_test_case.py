"""Shared test case and execution utilities for session command tests.

Provides ``SessionTestCase`` (the data model) and ``execute_session_command``
(the lifecycle runner) used by both commitTransaction and abortTransaction tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.executor import execute_command


class SessionOp(Enum):
    """Operation types that can be executed inside a transaction."""

    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


@dataclass(frozen=True)
class SessionOperation:
    """A single operation to execute inside a transaction.

    Attributes:
        op: The operation type.
        document: For INSERT, the document to insert.
        filter: For UPDATE/DELETE, the query filter.
        update: For UPDATE, the update document.
    """

    op: SessionOp
    document: dict[str, Any] | None = None
    filter: dict[str, Any] | None = None
    update: dict[str, Any] | None = None

    def execute(self, collection: Collection, session: Any) -> None:
        """Execute this operation against the collection within the session."""
        if self.op == SessionOp.INSERT:
            collection.insert_one(self.document, session=session)
        elif self.op == SessionOp.UPDATE:
            assert self.filter is not None and self.update is not None
            collection.update_one(self.filter, self.update, session=session)
        elif self.op == SessionOp.DELETE:
            assert self.filter is not None
            collection.delete_one(self.filter, session=session)


@dataclass(frozen=True)
class SessionTestCase(CommandTestCase):
    """Test case for session command success tests (e.g. commitTransaction).

    Extends CommandTestCase to model a multi-step transaction workflow:
    seed documents, run operations inside a transaction, commit, and
    verify the result via readback or commit response.

    Attributes:
        ops: Operations to execute inside the transaction before committing.
        commit_command: Optional raw command dict for committing (e.g. to
            include writeConcern or comment). When None, uses
            ``session.commit_transaction()``.
        expected_response: Expected fields from the commit command response.
            When set, the assertion targets the commit response instead of
            a readback query. Defaults to ``None``.
            Mutually exclusive with ``expected``.
        readback_filter: Filter for the post-commit readback query. Defaults
            to ``{}``.
        readback_sort: Sort for the post-commit readback query. Defaults
            to ``{"_id": 1}``.
    """

    ops: list[SessionOperation] = field(default_factory=list)
    commit_command: dict[str, Any] | None = None
    expected_response: dict[str, Any] | None = None
    readback_filter: dict[str, Any] = field(default_factory=dict)
    readback_sort: dict[str, Any] = field(default_factory=lambda: {"_id": 1})


def execute_session_command(
    collection: Collection, test_case: SessionTestCase, *, abort: bool = False
) -> Any:
    """Execute a SessionTestCase: seed, transact, commit or abort, and return the result.

    Runs the full transaction lifecycle described by *test_case*:

    1. Seed ``test_case.docs`` into *collection*.
    2. Open a client session and start a transaction.
    3. Execute each ``SessionOperation`` in ``test_case.ops``.
    4. End the transaction:
       - If ``test_case.commit_command`` is set, send it as a raw admin command.
       - Otherwise, commit or abort via the session method (based on *abort*).
    5. Return the appropriate result for assertion:
       - If ``test_case.expected_response`` is set, return the command response.
       - Otherwise, return the readback query result via ``execute_command``.

    When *abort* is True and a command response is expected, the function also
    verifies that the aborted transaction's data did not persist.

    Args:
        collection: The pytest ``collection`` fixture.
        test_case: A ``SessionTestCase`` instance.
        abort: If True, abort the transaction instead of committing.

    Returns:
        Result dict (command response or readback) or Exception.
    """
    # 1. Seed documents.
    if test_case.docs is not None:
        if test_case.docs:
            collection.insert_many(test_case.docs)

    # 2-4. Transaction lifecycle.
    client = collection.database.client
    command_result: dict[str, Any] | Exception | None = None
    with client.start_session() as session:
        session.start_transaction()
        for op in test_case.ops:
            op.execute(collection, session)
        if test_case.commit_command is not None:
            try:
                command_result = client.admin.command(test_case.commit_command, session=session)
            except Exception as e:
                command_result = e
        elif abort:
            session.abort_transaction()
        else:
            session.commit_transaction()

    # 5. Return command response or readback.
    if test_case.expected_response is not None:
        if abort and not isinstance(command_result, Exception) and test_case.ops:
            # Verify that aborted data did NOT persist (the raw admin
            # command path bypasses pymongo's session bookkeeping; we
            # assert rollback explicitly by checking that transacted
            # inserts are not visible after abort).
            readback = execute_command(
                collection,
                {"find": collection.name, "filter": test_case.readback_filter},
            )
            assert not isinstance(readback, Exception), f"Readback after abort failed: {readback}"
            cursor = readback.get("cursor", {})
            docs = cursor.get("firstBatch", [])
            seed_count = len(test_case.docs) if test_case.docs else 0
            assert len(docs) == seed_count, (
                f"Aborted transaction data persisted — "
                f"expected {seed_count} docs (seed only), got {len(docs)}"
            )
        else:
            execute_command(collection, {"find": collection.name, "filter": {}})
        return command_result

    return execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test_case.readback_filter,
            "sort": test_case.readback_sort,
        },
    )
