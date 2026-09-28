"""Shared infrastructure for $searchMeta stage tests."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.fixtures import cleanup_database, generate_database_name


@dataclass(frozen=True)
class CollectionFixtureTestCase(StageTestCase):
    """A $searchMeta case whose collection is supplied by a named fixture.

    ``collection_fixture`` names the module-scoped fixture that builds the
    search-indexed collection, letting cases targeting different collection
    states share one parametrized test. A test using this must declare
    ``engine_client`` directly so target parametrization fires before the
    fixture resolves via ``request.getfixturevalue``.
    """

    collection_fixture: str = ""


# Shared dataset; the match counts the tests assert are derived from these
# documents.
SEARCH_DOCS: list[dict[str, Any]] = [
    {"_id": 1, "title": "the quick brown fox", "n": 1, "cat": "a"},
    {"_id": 2, "title": "quick red fox", "n": 5, "cat": "b"},
    {"_id": 3, "title": "lazy brown dog", "n": 10, "cat": "a"},
    {"_id": 4, "title": "slow green turtle", "n": 15, "cat": "c"},
    {"_id": 5, "title": "quick small mouse", "n": 20, "cat": "b"},
]

# Match count for the large collection, chosen to exceed the lower-bound count's
# exact-count threshold. Referenced by the fixture and the test expectations.
LARGE_MATCH_COUNT = 10_000


def wait_for_ready(db: Database, name: str) -> None:
    """Block until every search index on the collection reports READY."""
    # A search index build is asynchronous; allow generous time to reach READY.
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        batch = db.command({"listSearchIndexes": name})["cursor"]["firstBatch"]
        if batch and all(idx.get("status") == "READY" for idx in batch):
            return
        time.sleep(1)
    raise TimeoutError(f"search index on {name!r} did not reach READY")


@contextmanager
def build_collection(
    engine_client, worker_id, tag: str, coll_name: str, docs, indexes
) -> Iterator[Collection]:
    """Yield a module-scoped collection built from a single recipe.

    ``tag`` namespaces the database so distinct fixtures and modules never
    collide. ``docs=None`` leaves the collection uncreated, ``docs=[]`` creates
    it empty, and a non-empty list creates and populates it. When ``indexes`` is
    given they are built as search indexes and awaited to READY.
    """
    db_name = generate_database_name(tag, worker_id)
    # Database name is deterministic, so drop any leftover from a crashed run.
    cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db[coll_name]
    try:
        if docs is None:
            pass
        elif docs:
            coll.insert_many(docs)
        else:
            db.create_collection(coll.name)
        if indexes:
            db.command({"createSearchIndexes": coll.name, "indexes": indexes})
            wait_for_ready(db, coll.name)
        yield coll
    finally:
        cleanup_database(engine_client, db_name)


@contextmanager
def open_search_collection(engine_client, worker_id, tag: str) -> Iterator[Collection]:
    """Yield the standard metadata search collection.

    Carries a "default" and a non-default "alt_idx" index so index-selection
    cases can target each by name.
    """
    with build_collection(
        engine_client,
        worker_id,
        tag,
        "searchmeta",
        SEARCH_DOCS,
        [
            {"name": "default", "definition": {"mappings": {"dynamic": True}}},
            {"name": "alt_idx", "definition": {"mappings": {"dynamic": True}}},
        ],
    ) as coll:
        yield coll
