"""Extended test case for $indexStats tests with target_collection."""

from __future__ import annotations

from dataclasses import dataclass, field

from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.target_collection import TargetCollection


@dataclass(frozen=True)
class IndexStatsTestCase(StageTestCase):
    """StageTestCase with declarative target_collection support."""

    target_collection: TargetCollection = field(default_factory=TargetCollection)


def prepare_collection(collection: Collection, test_case: IndexStatsTestCase) -> Collection:
    """Resolve target collection and set up docs/indexes.

    Returns the resolved collection to run the aggregate against.
    """
    if test_case.docs is None:
        return collection

    db = collection.database
    db.create_collection(collection.name)
    coll = test_case.target_collection.resolve(db, collection)

    if test_case.docs:
        coll.insert_many(test_case.docs)
    if test_case.indexes:
        coll.create_indexes(test_case.indexes)
    return coll
