"""Shared test case for collection command tests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class CommandContext:
    """Runtime fixture values available to command test cases.

    Attributes:
        collection: The fixture collection name.
        database: The fixture database name.
        namespace: The fully qualified namespace (database.collection).
    """

    collection: str
    database: str
    namespace: str

    @classmethod
    def from_collection(cls, collection) -> CommandContext:
        db = collection.database.name
        coll = collection.name
        return cls(collection=coll, database=db, namespace=f"{db}.{coll}")


@dataclass(frozen=True)
class CommandTestCase(BaseTestCase):
    """Test case for collection command tests.

    Collection commands often reference fixture-dependent values like
    collection names and namespaces. Fields that need these values accept
    a callable that receives a CommandContext at execution time.

    Attributes:
        setup: A callable that receives a Database and returns the
            Collection to execute against. When None, uses the default
            fixture collection.
        docs: Documents to insert before executing the command.
        command: A callable (CommandContext -> dict) for commands that
            need fixture values, or a plain dict.
        expected: A callable (CommandContext -> dict) for results that
            need fixture values, a plain dict, or None for error cases.
    """

    setup: Callable[[Database], Collection] | None = None
    docs: list[dict[str, Any]] | None = None
    command: dict[str, Any] | Callable[[CommandContext], dict[str, Any]] | None = None
    expected: dict[str, Any] | Callable[[CommandContext], dict[str, Any]] | None = None

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
