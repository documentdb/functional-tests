"""Package-scoped fixtures for $vectorSearch stage tests.

Each vectorSearch index is heavyweight (created, then polled until READY), so the
corpora and indexes are built once per package here rather than per test file."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.framework.test_constants import DOUBLE_ZERO

from .utils.vectorSearch_common import (
    _FILTER_OID_A,
    _FILTER_OID_B,
    _FILTER_UUID_A,
    _FILTER_UUID_B,
)

_VECTOR_CORPUS = [
    {
        "_id": 1,
        "vc": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
        "ve": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
        "vd": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
        "v8": [1.0] + [DOUBLE_ZERO] * 7,
        "meta": {"vec": [1.0, DOUBLE_ZERO, DOUBLE_ZERO]},
        "cat": "x",
        "year": 1999,
        "count": Int64(10),
        "rating": 4.5,
        "active": True,
        "oid": _FILTER_OID_A,
        "uid": _FILTER_UUID_A,
        "created": datetime(2020, 1, 1, tzinfo=timezone.utc),
        "tags": ["x", "y"],
        "opt": "p",
        "name": "a",
    },
    {
        "_id": 2,
        "vc": [0.8, 0.2, DOUBLE_ZERO],
        "ve": [0.8, 0.2, DOUBLE_ZERO],
        "vd": [0.8, 0.2, DOUBLE_ZERO],
        "v8": [DOUBLE_ZERO, 1.0] + [DOUBLE_ZERO] * 6,
        "meta": {"vec": [0.8, 0.2, DOUBLE_ZERO]},
        "cat": "x",
        "year": 2000,
        "count": Int64(20),
        "rating": 3.0,
        "active": False,
        "oid": _FILTER_OID_B,
        "uid": _FILTER_UUID_B,
        "created": datetime(2021, 6, 15, tzinfo=timezone.utc),
        "tags": ["y", "z"],
        "opt": "p",
        "name": "b",
    },
    {
        "_id": 3,
        "vc": [0.6, 0.4, DOUBLE_ZERO],
        "ve": [0.6, 0.4, DOUBLE_ZERO],
        "vd": [0.6, 0.4, DOUBLE_ZERO],
        "v8": [DOUBLE_ZERO] * 2 + [1.0] + [DOUBLE_ZERO] * 5,
        "meta": {"vec": [0.6, 0.4, DOUBLE_ZERO]},
        "cat": "y",
        "year": 2001,
        "count": Int64(30),
        "rating": 5.0,
        "active": True,
        "oid": _FILTER_OID_A,
        "uid": _FILTER_UUID_A,
        "created": datetime(2022, 12, 31, tzinfo=timezone.utc),
        "tags": ["z"],
        "opt": None,
        "name": "c",
    },
    {
        "_id": 4,
        "vc": [0.2, 0.8, DOUBLE_ZERO],
        "ve": [0.2, 0.8, DOUBLE_ZERO],
        "vd": [0.2, 0.8, DOUBLE_ZERO],
        "v8": [DOUBLE_ZERO] * 3 + [1.0] + [DOUBLE_ZERO] * 4,
        "meta": {"vec": [0.2, 0.8, DOUBLE_ZERO]},
        "cat": "y",
        "year": 2010,
        "count": Int64(40),
        "rating": 2.0,
        "active": False,
        "oid": _FILTER_OID_B,
        "uid": _FILTER_UUID_B,
        "created": datetime(2023, 3, 3, tzinfo=timezone.utc),
        "tags": [],
        "name": "d",
    },
    {
        "_id": 5,
        "vc": [DOUBLE_ZERO, 1.0, DOUBLE_ZERO],
        "ve": [DOUBLE_ZERO, 1.0, DOUBLE_ZERO],
        "vd": [DOUBLE_ZERO, 1.0, DOUBLE_ZERO],
        "v8": [DOUBLE_ZERO] * 4 + [1.0] + [DOUBLE_ZERO] * 3,
        "meta": {"vec": [DOUBLE_ZERO, 1.0, DOUBLE_ZERO]},
        "cat": "y",
        "year": 2010,
        "count": Int64(50),
        "rating": 4.0,
        "active": True,
        "oid": _FILTER_OID_A,
        "uid": _FILTER_UUID_A,
        "created": datetime(2024, 7, 7, tzinfo=timezone.utc),
        "tags": ["x"],
        "name": "e",
    },
]

# Mirror each document's cosine vector under a precomposed (NFC) Unicode field
# name (precomposed e-acute, U+00E9) so the index has a real Unicode-named vector
# path to contrast against the decomposed (NFD) query form.
for _doc in _VECTOR_CORPUS:
    _doc["caf\u00e9_vec"] = _doc["vc"]
    _doc["v8c"] = _doc["v8"]

_INDEX_READY_TIMEOUT_SECONDS = 120


@pytest.fixture(scope="package")
def vector_search_collection(engine_client, worker_id):
    """Provide a collection with a READY cosine vectorSearch index over a fixed corpus."""
    db_name = f"vs_core_{worker_id}"
    db = engine_client[db_name]
    coll = db["vectors"]
    db.drop_collection(coll.name)
    db.create_collection(coll.name)
    coll.insert_many([dict(doc) for doc in _VECTOR_CORPUS])
    db.command(
        {
            "createSearchIndexes": coll.name,
            "indexes": [
                {
                    "name": "vs_core_index",
                    "type": "vectorSearch",
                    "definition": {
                        "fields": [
                            {
                                "type": "vector",
                                "path": "vc",
                                "numDimensions": 3,
                                "similarity": "cosine",
                            },
                            {
                                "type": "vector",
                                "path": "ve",
                                "numDimensions": 3,
                                "similarity": "euclidean",
                            },
                            {
                                "type": "vector",
                                "path": "vd",
                                "numDimensions": 3,
                                "similarity": "dotProduct",
                            },
                            {"type": "filter", "path": "cat"},
                            {"type": "filter", "path": "year"},
                            {"type": "filter", "path": "count"},
                            {"type": "filter", "path": "rating"},
                            {"type": "filter", "path": "active"},
                            {"type": "filter", "path": "oid"},
                            {"type": "filter", "path": "uid"},
                            {"type": "filter", "path": "created"},
                            {"type": "filter", "path": "tags"},
                            {"type": "filter", "path": "opt"},
                            {
                                "type": "vector",
                                "path": "v8",
                                "numDimensions": 8,
                                "similarity": "euclidean",
                            },
                            {
                                "type": "vector",
                                "path": "v8c",
                                "numDimensions": 8,
                                "similarity": "cosine",
                            },
                            {
                                "type": "vector",
                                "path": "meta.vec",
                                "numDimensions": 3,
                                "similarity": "cosine",
                            },
                            {
                                "type": "vector",
                                "path": "caf\u00e9_vec",
                                "numDimensions": 3,
                                "similarity": "cosine",
                            },
                        ]
                    },
                }
            ],
        }
    )
    deadline = time.monotonic() + _INDEX_READY_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        indexes = list(coll.aggregate([{"$listSearchIndexes": {}}]))
        if indexes and indexes[0].get("status") == "READY":
            break
        time.sleep(2)
    else:
        raise TimeoutError("vectorSearch index did not reach READY state")
    yield coll
    engine_client.drop_database(db_name)


@pytest.fixture(scope="package")
def vector_search_no_index_collection(engine_client, worker_id):
    """Provide an empty collection with no vectorSearch index for spec-error tests."""
    db_name = f"vs_core_noindex_{worker_id}"
    db = engine_client[db_name]
    coll = db["vectors"]
    db.drop_collection(coll.name)
    db.create_collection(coll.name)
    yield coll
    engine_client.drop_database(db_name)


@pytest.fixture(scope="package")
def vector_search_absent_collection(engine_client, worker_id):
    """Provide a handle to a collection that does not exist (never created)."""
    db_name = f"vs_core_absent_{worker_id}"
    db = engine_client[db_name]
    coll = db["absent_vectors"]
    db.drop_collection(coll.name)
    yield coll
    engine_client.drop_database(db_name)
