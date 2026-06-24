"""Shared test case for session command tests (e.g. commitTransaction, abortTransaction)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)


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
