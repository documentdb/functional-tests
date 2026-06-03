"""Shared test case for collection command tests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pymongo import IndexModel
from pymongo.collection import Collection
from pymongo.database import Database

from documentdb_tests.framework.target_collection import (
    SiblingCollection,
    TargetCollection,
)
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class CommandContext:
    """Runtime context passed to command/expected callables.

    Attributes:
        collection: The resolved collection name.
        database: The resolved database name.
        namespace: The full namespace string (``database.collection``).
        uuids: Mapping of collection names to their server-assigned UUIDs.
    """

    collection: str
    database: str
    namespace: str
    uuids: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_collection(cls, collection: Collection) -> CommandContext:
        db_obj = collection.database
        db = db_obj.name
        coll_name = collection.name
        uuids = {}
        for info in db_obj.list_collections():
            coll_info = info.get("info", {})
            if "uuid" in coll_info:
                uuids[info["name"]] = coll_info["uuid"]
        return cls(collection=coll_name, database=db, namespace=f"{db}.{coll_name}", uuids=uuids)


@dataclass(frozen=True)
class CommandTestCase(BaseTestCase):
    """Test case for collection command tests.

    Collection commands often reference fixture-dependent values like
    collection names and namespaces. Fields that need these values accept
    a callable that receives a CommandContext at execution time.

    Attributes:
        target_collection: Describes the collection to execute against.
            Defaults to the fixture collection.
        siblings: Optional additional collections to create alongside the
            source before executing the command.
        indexes: Indexes to create before executing the command. Each
            entry is passed to create_index.
        docs: Documents to insert before executing the command.
        command: A callable (CommandContext -> dict) for commands that
            need fixture values, or a plain dict.
        expected: A callable (CommandContext -> dict) for results that
            need fixture values, a plain dict, a list of dicts, or None
            for error cases.
        ignore_order_in: Optional names of result fields whose array contents
            should be compared without regard to element order.
    """

    target_collection: TargetCollection = field(default_factory=TargetCollection)
    siblings: list[SiblingCollection] | None = None
    indexes: list[IndexModel] | None = None
    docs: list[dict[str, Any]] | None = None
    command: dict[str, Any] | Callable[..., dict[str, Any]] | None = None
    expected: dict[str, Any] | list[dict[str, Any]] | Callable[..., dict[str, Any]] | None = None
    ignore_order_in: list[str] | None = None

    def prepare(self, db: Database, collection: Collection) -> Collection:
        """Resolve the target collection and apply indexes/docs.

        Documents and indexes are inserted into the collection returned
        by ``target_collection.writable(source, resolved)``. For views
        this is the source; for regular collections it is the resolved
        collection itself.

        - If ``docs=None``, the collection is not created and will not exist.
        - If ``docs=[]``, the collection is explicitly created but left empty.
        - If ``docs=[...]``, the collection is created and documents are inserted.
        """
        resolved = self.target_collection.resolve(db, collection)
        target = self.target_collection.writable(collection, resolved)
        if self.indexes:
            target.create_indexes(self.indexes)
        if self.docs is not None:
            if target.name not in target.database.list_collection_names():
                target.database.create_collection(target.name)
            if self.docs:
                target.insert_many(self.docs)
        if self.siblings:
            for sibling in self.siblings:
                sibling.create(db, resolved)
        return resolved

    def build_command(self, ctx: CommandContext) -> dict[str, Any]:
        """Resolve the command dict from a callable or plain dict."""
        if self.command is None:
            raise ValueError(f"CommandTestCase '{self.id}' has no command defined")
        if isinstance(self.command, dict):
            return self.command
        return self.command(ctx)

    def build_expected(self, ctx: CommandContext) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Resolve expected from a callable or plain value."""
        if self.expected is None or isinstance(self.expected, (dict, list)):
            return self.expected
        return self.expected(ctx)


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
            collection.update_one(self.filter, self.update, session=session)
        elif self.op == SessionOp.DELETE:
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
            a readback query. Mutually exclusive with ``expected``.
        readback_filter: Filter for the post-commit readback query. Defaults
            to ``{}``. Ignored when ``expected_response`` is set.
        readback_sort: Sort for the post-commit readback query. Defaults
            to ``{"_id": 1}``.
    """

    ops: list[SessionOperation] = field(default_factory=list)
    commit_command: dict[str, Any] | None = None
    expected_response: dict[str, Any] | None = None
    readback_filter: dict[str, Any] = field(default_factory=dict)
    readback_sort: dict[str, Any] = field(default_factory=lambda: {"_id": 1})
