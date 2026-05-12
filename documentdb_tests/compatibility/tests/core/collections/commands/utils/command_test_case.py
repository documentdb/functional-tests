"""Shared test case for collection command tests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pymongo import IndexModel
from pymongo.collection import Collection
from pymongo.database import Database

from documentdb_tests.framework.target_collection import (
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
    """

    collection: str
    database: str
    namespace: str

    @classmethod
    def from_collection(cls, collection: Collection) -> CommandContext:
        db = collection.database.name
        coll_name = collection.name
        return cls(collection=coll_name, database=db, namespace=f"{db}.{coll_name}")


@dataclass(frozen=True)
class CommandTestCase(BaseTestCase):
    """Test case for collection command tests.

    Collection commands often reference fixture-dependent values like
    collection names and namespaces. Fields that need these values accept
    a callable that receives a CommandContext at execution time.

    Attributes:
        target_collection: Describes the collection to execute against.
            Defaults to the fixture collection.
        indexes: Indexes to create before executing the command. Each
            entry is passed to create_index.
        docs: Documents to insert before executing the command.
        command: A callable (CommandContext -> dict) for commands that
            need fixture values, or a plain dict.
        expected: A callable (CommandContext -> dict) for results that
            need fixture values, a plain dict, or None for error cases.
    """

    target_collection: TargetCollection = field(default_factory=TargetCollection)
    indexes: list[IndexModel] | None = None
    docs: list[dict[str, Any]] | None = None
    command: dict[str, Any] | Callable[[CommandContext], dict[str, Any]] | None = None
    expected: dict[str, Any] | Callable[[CommandContext], dict[str, Any]] | None = None

    def prepare(self, db: Database, collection: Collection) -> Collection:
        """Resolve the target collection and apply indexes/docs.

        - If ``docs=None``, the collection is not created and will not exist.
        - If ``docs=[]``, the collection is explicitly created but left empty.
        - If ``docs=[...]``, the collection is created and documents are inserted.
        """
        collection = self.target_collection.resolve(db, collection)
        if self.indexes:
            collection.create_indexes(self.indexes)
        if self.docs is not None:
            if collection.name not in collection.database.list_collection_names():
                collection.database.create_collection(collection.name)
            if self.docs:
                collection.insert_many(self.docs)
        return collection

    def build_command(self, ctx: CommandContext) -> dict[str, Any]:
        """Resolve the command dict from a callable or plain dict."""
        if self.command is None:
            raise ValueError(f"CommandTestCase '{self.id}' has no command defined")
        if isinstance(self.command, dict):
            return self.command
        return self.command(ctx)

    def build_expected(self, ctx: CommandContext) -> dict[str, Any] | None:
        """Resolve expected from a callable or plain value."""
        if self.expected is None or isinstance(self.expected, dict):
            return self.expected
        return self.expected(ctx)
