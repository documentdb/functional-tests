"""Shared Queryable Encryption collection fixtures for tests in this directory.

Creating a QE collection needs a per-field keyId, and each test file here needs
a differently-shaped one. The fixtures here are the single source of truth;
this directory's conftest re-exports them so every test file picks them up.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from bson import Binary
from pymongo.collection import Collection


def _create_qe_collection(
    collection: Collection, name: str, fields: list[dict[str, Any]]
) -> Collection:
    """Create and return a Queryable Encryption collection with the given fields."""
    db = collection.database
    resolved_fields = [{**field, "keyId": Binary(uuid4().bytes, 4)} for field in fields]
    db.command("create", name, encryptedFields={"fields": resolved_fields})
    return db[name]


@pytest.fixture()
def qe_collection(collection):
    """A Queryable Encryption collection with ssn as encrypted field."""
    qe = _create_qe_collection(
        collection,
        f"{collection.name}_qe",
        [{"path": "ssn", "bsonType": "string", "queries": {"queryType": "equality"}}],
    )
    yield qe
    qe.database.drop_collection(qe.name)


@pytest.fixture()
def qe_collection_multi(collection):
    """A Queryable Encryption collection with two independent encrypted fields."""
    qe = _create_qe_collection(
        collection,
        f"{collection.name}_qe_multi",
        [
            {"path": "ssn", "bsonType": "string"},
            {"path": "dob", "bsonType": "string"},
        ],
    )
    yield qe
    qe.database.drop_collection(qe.name)


@pytest.fixture()
def qe_collection_nested(collection):
    """A Queryable Encryption collection with address.ssn as a nested encrypted path."""
    qe = _create_qe_collection(
        collection,
        f"{collection.name}_qe_nested",
        [{"path": "address.ssn", "bsonType": "string"}],
    )
    yield qe
    qe.database.drop_collection(qe.name)
