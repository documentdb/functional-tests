"""Helpers for $listClusterCatalog aggregation tests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database

from documentdb_tests.framework.target_collection import TargetCollection
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class StageContext:
    """Runtime context for $listClusterCatalog test cases.

    Attributes:
        collection: The resolved collection name.
        ns: The full namespace string (``database.collection``).
    """

    collection: str
    ns: str

    @classmethod
    def from_collection(cls, coll: Collection) -> StageContext:
        return cls(
            collection=coll.name,
            ns=f"{coll.database.name}.{coll.name}",
        )


@dataclass(frozen=True)
class ListClusterCatalogTestCase(BaseTestCase):
    """Data-driven test case for $listClusterCatalog.

    Provide either ``pipeline`` (builds a database-level aggregate command
    automatically) or ``command`` (full command dict).

    Attributes:
        target_collection: Resolves the execution target collection.
        docs: Controls collection creation in the fixture database.
            ``None`` means the collection will not exist.
            ``[]`` means the collection is explicitly created but left empty.
        pipeline: A list or callable ``(ctx) -> list`` for the pipeline.
        command: Full aggregate command dict (mutually exclusive with pipeline).
    """

    target_collection: TargetCollection = field(default_factory=TargetCollection)
    docs: list[dict[str, Any]] | None = None
    pipeline: list | Callable | None = None
    command: dict[str, Any] | Callable | None = None

    def __post_init__(self):
        super().__post_init__()
        if self.pipeline and self.command is not None:
            raise ValueError(
                f"ListClusterCatalogTestCase '{self.id}':"
                " pipeline and command are mutually exclusive"
            )

    def prepare(self, db: Database, collection: Collection) -> Collection:
        """Resolve target collection and create if needed."""
        coll = self.target_collection.resolve(db, collection)
        if self.docs is not None:
            if collection.name not in db.list_collection_names():
                db.create_collection(collection.name)
            if self.docs:
                collection.insert_many(self.docs)
        return coll

    def build_command(self, collection: Collection, ctx: StageContext) -> dict[str, Any]:
        """Build the aggregate command dict."""
        if self.command is not None:
            cmd: dict[str, Any] = self.command(ctx) if callable(self.command) else self.command
            return cmd
        pipeline = self.pipeline(ctx) if callable(self.pipeline) else self.pipeline
        return {"aggregate": 1, "pipeline": pipeline, "cursor": {}}
