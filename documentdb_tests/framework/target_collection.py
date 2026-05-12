"""Collection target types for tests.

Each subclass describes a kind of collection a test needs and knows how
to create it from the fixture collection. All derived names use the
fixture name as a prefix to guarantee parallel-safe uniqueness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
class SystemViewsCollection(ViewCollection):
    """The system.views collection, populated by creating a view."""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        view_name = f"{collection.name}_view"
        db.command("create", view_name, viewOn=collection.name, pipeline=[])
        return db["system.views"]


@dataclass(frozen=True)
class CappedCollection(TargetCollection):
    """A capped collection."""

    size: int = 4096
    max: int | None = None

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_capped"
        kwargs: dict[str, Any] = {"capped": True, "size": self.size}
        if self.max is not None:
            kwargs["max"] = self.max
        db.create_collection(name, **kwargs)
        return db[name]


@dataclass(frozen=True)
class NamedCollection(TargetCollection):
    """A collection with a custom name suffix."""

    suffix: str = ""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}{self.suffix}"
        db.create_collection(name)
        return db[name]


@dataclass(frozen=True)
class TargetDatabase(TargetCollection):
    """Run the command against a collection in a new database.

    The fixture database name is used as a prefix to guarantee
    parallel-safe uniqueness. The resulting database should be
    registered for cleanup via the ``register_db_cleanup`` fixture.
    """

    suffix: str = ""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{db.name}_{self.suffix}"
        return collection.database.client[name]["tmp"]


@dataclass(frozen=True)
class ExistingDatabase(TargetCollection):
    """Run the command against a collection in an existing database."""

    db_name: str = ""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        return collection.database.client[self.db_name]["tmp"]


@dataclass(frozen=True)
class TimeseriesCollection(TargetCollection):
    """A time series collection."""

    time_field: str = "ts"
    meta_field: str = "meta"
    granularity: str | None = None

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_ts"
        ts_opts: dict[str, Any] = {
            "timeField": self.time_field,
            "metaField": self.meta_field,
        }
        if self.granularity is not None:
            ts_opts["granularity"] = self.granularity
        db.create_collection(name, timeseries=ts_opts)
        return db[name]
