"""
Shared test case for pipeline stage tests.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pymongo.collection import Collection

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class StageTestCase(BaseTestCase):
    """Test case for pipeline stage tests."""

    docs: list[dict[str, Any]] | None = None
    pipeline: list[dict[str, Any]] = field(default_factory=list)
    setup: Callable | None = None


def populate_collection(collection: Collection, test_case: StageTestCase) -> None:
    """Set up the collection for a stage test case.

    - If ``docs=None``, collection is not created, and will not exist.
    - If ``docs=[]``, collection is explicitly created but left empty.
    - If ``docs=[...]``, collection is created and documents are inserted.
    """
    if test_case.docs is None:
        return

    collection.database.create_collection(collection.name)
    if test_case.docs:
        collection.insert_many(test_case.docs)
