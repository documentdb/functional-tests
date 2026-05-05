"""Helpers for $collStats aggregation tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database

from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.target_collection import TargetCollection
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class CollStatsTestCase(BaseTestCase):
    """Data-driven test case for $collStats.

    Attributes:
        target_collection: Optional ``TargetCollection`` override.
        docs: Documents to insert before running the command.
            ``None`` means the collection will not exist.
        pipeline: The full aggregation pipeline to execute.
        checks: Property checks for ``assertProperties``.
    """

    target_collection: TargetCollection = field(default_factory=TargetCollection)
    docs: list[dict[str, Any]] | None = None
    pipeline: list[dict[str, Any]] = field(default_factory=list)
    checks: dict[str, Any] | None = None

    def prepare(self, db: Database, collection: Collection) -> Collection:
        """Resolve target collection and insert docs."""
        coll = self.target_collection.resolve(db, collection)
        if self.docs is not None:
            if self.docs:
                coll.insert_many(self.docs)
            else:
                db.create_collection(coll.name)
        return coll

    def assert_result(self, result: Any) -> None:
        """Assert the result matches expected checks or error code."""
        if self.error_code:
            assertFailureCode(result, self.error_code, msg=self.msg)
        elif self.checks is not None:
            assertProperties(result, self.checks, msg=self.msg)
