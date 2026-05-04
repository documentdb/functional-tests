"""Collection target types for tests.

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
