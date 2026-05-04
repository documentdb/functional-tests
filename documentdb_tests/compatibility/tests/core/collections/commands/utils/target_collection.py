"""Collection target types for command tests.

Each subclass describes a kind of collection a test needs and knows how
to create it from the fixture collection. All derived names use the
fixture name as a prefix to guarantee parallel-safe uniqueness.
"""

from __future__ import annotations

from dataclasses import dataclass

from pymongo.collection import Collection
from pymongo.database import Database

from documentdb_tests.framework.target_collection import TargetCollection


@dataclass(frozen=True)
class ViewCollection(TargetCollection):
    """A view on the fixture collection."""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        view_name = f"{collection.name}_view"
        db.command("create", view_name, viewOn=collection.name, pipeline=[])
        return db[view_name]


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
class CappedCollection(TargetCollection):
    """A capped collection."""

    size: int = 4096
    max: int = 0

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_capped"
        kwargs: dict = {"capped": True, "size": self.size}
        if self.max:
            kwargs["max"] = self.max
        db.create_collection(name, **kwargs)
        return db[name]


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
class TimeseriesCollection(TargetCollection):
    """A timeseries collection."""

    def resolve(self, db: Database, collection: Collection) -> Collection:
        name = f"{collection.name}_ts"
        db.create_collection(name, timeseries={"timeField": "ts"})
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
