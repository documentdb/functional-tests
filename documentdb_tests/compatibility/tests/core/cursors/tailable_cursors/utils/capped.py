"""Shared utilities for tailable cursor tests."""

from __future__ import annotations

from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database

from documentdb_tests.framework.target_collection import CappedCollection


def create_capped(
    db: Database,
    collection: Collection,
    docs: list[dict[str, Any]],
    **kwargs: Any,
) -> Collection:
    """Create a capped collection and insert docs."""
    capped = CappedCollection(**kwargs).resolve(db, collection)
    if docs:
        capped.insert_many(docs)
    return capped
