"""Collection target types for tests.

Each subclass describes a kind of collection a test needs and knows how
to create it from the fixture collection. All derived names use the
fixture name as a prefix to guarantee parallel-safe uniqueness.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
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
class CustomCollection(TargetCollection):
    """A collection created with arbitrary options.

    Pass any keyword arguments accepted by ``create`` as the ``options``
    dict.
    """

    options: dict[str, Any] = field(default_factory=dict)

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_custom"
        db.command("create", name, **self.options)
        return db[name]


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
    """A collection with a custom name suffix.

    suffix can be a static string or a callable (db_name, coll_name) -> str
    for cases where the suffix depends on runtime values.
    """

    suffix: str | Callable[[str, str], str] = ""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        s = self.suffix(db.name, collection.name) if callable(self.suffix) else self.suffix
        name = f"{collection.name}{s}"
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
class ViewChainCollection(TargetCollection):
    """A chain of views on the fixture collection."""

    depth: int = 1

    def resolve(self, db: Database, collection: Collection) -> Collection:
        source = collection.name
        for i in range(1, self.depth + 1):
            name = f"{collection.name}_chain_{i}"
            db.command("create", name, viewOn=source, pipeline=[])
            source = name
        return db[source]


@dataclass(frozen=True)
class ExistingCollection(TargetCollection):
    """A collection with an exact name (not derived from the fixture).

    Analogous to ExistingDatabase but for collection names.
    """

    name: str = ""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        return db[self.name]


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


@dataclass(frozen=True)
class SystemBucketsCollection(TimeseriesCollection):
    """The system.buckets collection, populated by creating a timeseries collection."""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_ts"
        ts_opts: dict[str, Any] = {
            "timeField": self.time_field,
            "metaField": self.meta_field,
        }
        if self.granularity is not None:
            ts_opts["granularity"] = self.granularity
        db.create_collection(name, timeseries=ts_opts)
        return db[f"system.buckets.{name}"]


@dataclass(frozen=True)
class ViewWithPipelineCollection(TargetCollection):
    """A view on the fixture collection with a non-empty pipeline."""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        view_name = f"{collection.name}_vpipe"
        db.command(
            "create",
            view_name,
            viewOn=collection.name,
            pipeline=[{"$match": {"x": 1}}],
        )
        return db[view_name]


@dataclass(frozen=True)
class ValidatedCollection(TargetCollection):
    """A collection with a JSON schema validator."""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_validated"
        db.create_collection(
            name,
            validator={"$jsonSchema": {"bsonType": "object", "required": ["x"]}},
            validationLevel="strict",
            validationAction="error",
        )
        return db[name]


@dataclass(frozen=True)
class CollatedCollection(TargetCollection):
    """A collection with a collation."""

    locale: str = "en"

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_collated"
        db.create_collection(name, collation={"locale": self.locale})
        return db[name]


@dataclass(frozen=True)
class ClusteredCollection(TargetCollection):
    """A user-created clustered collection."""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_clustered"
        db.create_collection(name, clusteredIndex={"key": {"_id": 1}, "unique": True})
        return db[name]


@dataclass(frozen=True)
class TimeseriesTTLCollection(TargetCollection):
    """A timeseries collection with TTL."""

    expire_after_seconds: int = 3600

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_ts_ttl"
        db.create_collection(
            name,
            timeseries={"timeField": "ts"},
            expireAfterSeconds=self.expire_after_seconds,
        )
        return db[name]


@dataclass(frozen=True)
class TimeseriesCustomBucketCollection(TargetCollection):
    """A timeseries collection with custom bucket span."""

    bucket_seconds: int = 300

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_ts_bucket"
        db.create_collection(
            name,
            timeseries={
                "timeField": "ts",
                "bucketRoundingSeconds": self.bucket_seconds,
                "bucketMaxSpanSeconds": self.bucket_seconds,
            },
        )
        return db[name]


@dataclass(frozen=True)
class ChangeStreamPreAndPostImagesCollection(TargetCollection):
    """A collection with changeStreamPreAndPostImages enabled."""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_cspi"
        db.create_collection(name, changeStreamPreAndPostImages={"enabled": True})
        return db[name]


@dataclass(frozen=True)
class StorageEngineCollection(TargetCollection):
    """A collection with storageEngine and indexOptionDefaults."""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_storage"
        db.create_collection(
            name,
            storageEngine={"wiredTiger": {"configString": ""}},
            indexOptionDefaults={"storageEngine": {"wiredTiger": {"configString": ""}}},
        )
        return db[name]


@dataclass(frozen=True)
class GridFSCollection(TargetCollection):
    """A GridFS collection (creates fs.files and fs.chunks)."""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        import gridfs

        prefix = f"{collection.name}_gfs"
        fs = gridfs.GridFS(db, collection=prefix)
        fs.put(b"data", filename="test.txt")
        return db[f"{prefix}.files"]


@dataclass(frozen=True)
class ExtraCollections(TargetCollection):
    """Creates additional collections to populate the database."""

    count: int

    def resolve(self, db: Database, collection: Collection) -> Collection:
        for i in range(self.count):
            db.create_collection(f"{collection.name}_extra_{i}")
        return collection


@dataclass(frozen=True)
class SiblingCollection:
    """Describes an additional collection to create alongside the source.

    The collection is named ``{fixture_name}{suffix}`` and created with
    the specified options. Documents are inserted if provided.
    """

    suffix: str = "_target"
    view_on_source: bool = False
    timeseries_field: str | None = None
    docs: list[dict[str, Any]] | None = None

    def create(self, db: Database, collection: Collection) -> None:
        """Create the sibling collection."""
        name = f"{collection.name}{self.suffix}"
        if self.view_on_source:
            db.create_collection(name, viewOn=collection.name, pipeline=[])
        elif self.timeseries_field:
            db.create_collection(name, timeseries={"timeField": self.timeseries_field})
        else:
            db.create_collection(name)
        if self.docs:
            db[name].insert_many(self.docs)
