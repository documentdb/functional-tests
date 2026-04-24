"""Collection target types for command tests.

Each subclass describes a kind of collection a test needs and knows how
to create it from the fixture collection. All derived names use the
fixture name as a prefix to guarantee parallel-safe uniqueness.
"""

from __future__ import annotations

from dataclasses import dataclass

from pymongo.collection import Collection
from pymongo.database import Database


@dataclass(frozen=True)
class TargetCollection:
    """Default. Use the fixture collection as-is."""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        return collection


@dataclass(frozen=True)
class ViewCollection(TargetCollection):
    """A view on the fixture collection."""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        view_name = f"{collection.name}_view"
        db.command("create", view_name, viewOn=collection.name, pipeline=[])
        return db[view_name]


@dataclass(frozen=True)
class CappedCollection(TargetCollection):
    """A capped collection."""

    size: int = 4096

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_capped"
        db.create_collection(name, capped=True, size=self.size)
        return db[name]


@dataclass(frozen=True)
class NamedCollection(TargetCollection):
    """A collection with a custom name suffix."""

    suffix: str = ""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}{self.suffix}"
        db.create_collection(name)
        return db[name]
