"""
Shared test case for pipeline stage tests.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pymongo.collection import Collection
from pymongo.operations import IndexModel

from documentdb_tests.framework.target_collection import TargetCollection
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class StageTestCase(BaseTestCase):
    """Test case for pipeline stage tests."""

    target_collection: TargetCollection = field(default_factory=TargetCollection)
    indexes: list[IndexModel] | None = None
    docs: list[dict[str, Any]] | None = None
    setup: Callable | None = None
    pipeline: list[dict[str, Any]] = field(default_factory=list)


def populate_collection(collection: Collection, test_case: StageTestCase) -> Collection:
    """Set up the collection for a stage test case.

    Resolves ``target_collection``, then creates and populates it:

    - If ``docs=None``, collection is not created, and will not exist.
    - If ``docs=[]``, collection is explicitly created but left empty.
    - If ``docs=[...]``, collection is created and documents are inserted.

    Returns the resolved collection to run commands against.
    """
    if test_case.docs is None:
        if test_case.indexes:
            raise ValueError("indexes requires docs to be defined")
        return collection

    db = collection.database
    db.create_collection(collection.name)
    coll = test_case.target_collection.resolve(db, collection)

    if test_case.docs:
        coll.insert_many(test_case.docs)
    if test_case.indexes:
        coll.create_indexes(test_case.indexes)
    return coll
