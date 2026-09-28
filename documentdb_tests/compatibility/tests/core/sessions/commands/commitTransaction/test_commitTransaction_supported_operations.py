"""Tests for operations that are supported inside a transaction.

Reads (find), aggregation (including ``$count``, the supported counterpart to
the disallowed ``count`` command), writes (update, delete), and a range of other
CRUD/administration commands and query operators are accepted inside a
transaction. Each test runs the operation in the transaction and commits;
acceptance is asserted via the ``ok: 1`` command response (contrast the
disallowed-operations file, where the same operations would be rejected).
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]


def test_find_runs_in_transaction(collection):
    """A find issued inside a transaction returns the collection's documents."""
    collection.insert_one({"_id": 1})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            collection, {"find": collection.name, "filter": {}}, session=session
        )
        session.commit_transaction()
    assertSuccess(result, [{"_id": 1}])


def test_aggregate_count_runs_in_transaction(collection):
    """An aggregate with $count runs inside a transaction and returns the count."""
    collection.insert_many([{"_id": 1}, {"_id": 2}])
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            collection,
            {"aggregate": collection.name, "pipeline": [{"$count": "n"}], "cursor": {}},
            session=session,
        )
        session.commit_transaction()
    assertSuccess(result, [{"n": 2}])


def test_update_runs_in_transaction(collection):
    """An update issued inside a transaction is durable after commit."""
    collection.insert_one({"_id": 1, "x": "before"})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.update_one({"_id": 1}, {"$set": {"x": "after"}}, session=session)
        session.commit_transaction()
    readback = execute_command(collection, {"find": collection.name, "filter": {}})
    assertSuccess(readback, [{"_id": 1, "x": "after"}])


def test_delete_runs_in_transaction(collection):
    """A delete issued inside a transaction is durable after commit."""
    collection.insert_one({"_id": 1})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.delete_one({"_id": 1}, session=session)
        session.commit_transaction()
    readback = execute_command(collection, {"find": collection.name, "filter": {}})
    assertSuccess(readback, [])


def test_distinct_runs_in_transaction(collection):
    """The distinct command is accepted inside a transaction."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 2}])
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            collection, {"distinct": collection.name, "key": "x"}, session=session
        )
        session.commit_transaction()
    assertSuccessPartial(result, {"ok": 1.0})


def test_findAndModify_runs_in_transaction(collection):
    """The findAndModify command is accepted inside a transaction."""
    collection.insert_one({"_id": 1, "x": "before"})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            collection,
            {
                "findAndModify": collection.name,
                "query": {"_id": 1},
                "update": {"$set": {"x": "after"}},
            },
            session=session,
        )
        session.commit_transaction()
    assertSuccessPartial(result, {"ok": 1.0})


def test_bulkWrite_runs_in_transaction(collection):
    """The bulkWrite command is accepted inside a transaction."""
    client = collection.database.client
    namespace = f"{collection.database.name}.{collection.name}"
    with client.start_session() as session:
        session.start_transaction()
        result = execute_admin_command(
            collection,
            {
                "bulkWrite": 1,
                "ops": [{"insert": 0, "document": {"_id": 1}}],
                "nsInfo": [{"ns": namespace}],
            },
            session=session,
        )
        session.commit_transaction()
    assertSuccessPartial(result, {"ok": 1.0})


def test_create_collection_runs_in_transaction(collection):
    """Creating a collection inside a transaction is accepted."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(collection, {"create": f"{collection.name}_new"}, session=session)
        session.commit_transaction()
    assertSuccessPartial(result, {"ok": 1.0})


def test_createIndexes_on_new_collection_runs_in_transaction(collection):
    """createIndexes is accepted on a collection created earlier in the same transaction."""
    client = collection.database.client
    new_collection = f"{collection.name}_new"
    with client.start_session() as session:
        session.start_transaction()
        execute_command(collection, {"create": new_collection}, session=session)
        result = execute_command(
            collection,
            {"createIndexes": new_collection, "indexes": [{"key": {"x": 1}, "name": "x_1"}]},
            session=session,
        )
        session.commit_transaction()
    assertSuccessPartial(result, {"ok": 1.0})


def test_near_query_runs_in_transaction(collection):
    """A $near query runs inside a transaction (with a 2dsphere index)."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_one({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            collection,
            {
                "find": collection.name,
                "filter": {
                    "loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}
                },
            },
            session=session,
        )
        session.commit_transaction()
    assertSuccessPartial(result, {"ok": 1.0})


def test_nearSphere_query_runs_in_transaction(collection):
    """A $nearSphere query runs inside a transaction (with a 2dsphere index)."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_one({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            collection,
            {
                "find": collection.name,
                "filter": {
                    "loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}
                },
            },
            session=session,
        )
        session.commit_transaction()
    assertSuccessPartial(result, {"ok": 1.0})


def test_geoNear_stage_runs_in_transaction(collection):
    """A $geoNear aggregation stage runs inside a transaction (with a 2dsphere index)."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_one({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {
                        "$geoNear": {
                            "near": {"type": "Point", "coordinates": [0, 0]},
                            "distanceField": "d",
                            "spherical": True,
                        }
                    }
                ],
                "cursor": {},
            },
            session=session,
        )
        session.commit_transaction()
    assertSuccessPartial(result, {"ok": 1.0})
