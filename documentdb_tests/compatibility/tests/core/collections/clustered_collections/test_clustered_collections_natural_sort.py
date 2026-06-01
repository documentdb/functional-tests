"""Tests for CRUD operations and natural sort on clustered collections."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

from .utils.clustered_utils import create_clustered


# Property [Natural Sort Returns _id Order]: $natural sort on clustered
# collections returns documents in _id order, not insertion order.
@pytest.mark.collection_mgmt
def test_natural_sort_returns_id_order(collection):
    """Test $natural:1 returns _id order on clustered collection."""
    name = create_clustered(collection)
    db = collection.database
    db[name].insert_many([{"_id": "c", "v": 3}, {"_id": "a", "v": 1}, {"_id": "b", "v": 2}])
    result = execute_command(
        db[name],
        {"find": name, "projection": {"_id": 1}, "sort": {"$natural": 1}},
    )
    assertSuccess(
        result,
        [{"_id": "a"}, {"_id": "b"}, {"_id": "c"}],
        msg="$natural:1 should return documents in _id order",
    )


# Property [Natural Sort Reverse]: $natural:-1 returns documents in reverse
# _id order on clustered collections.
@pytest.mark.collection_mgmt
def test_natural_sort_reverse(collection):
    """Test $natural:-1 returns reverse _id order on clustered collection."""
    name = create_clustered(collection)
    db = collection.database
    db[name].insert_many([{"_id": "c", "v": 3}, {"_id": "a", "v": 1}, {"_id": "b", "v": 2}])
    result = execute_command(
        db[name],
        {"find": name, "projection": {"_id": 1}, "sort": {"$natural": -1}},
    )
    assertSuccess(
        result,
        [{"_id": "c"}, {"_id": "b"}, {"_id": "a"}],
        msg="$natural:-1 should return documents in reverse _id order",
    )


# Property [Default Order is _id Order]: queries without explicit sort return
# documents in _id order on clustered collections.
@pytest.mark.collection_mgmt
def test_default_order_is_id_order(collection):
    """Test default order returns _id order on clustered collection."""
    name = create_clustered(collection)
    db = collection.database
    db[name].insert_many([{"_id": "c", "v": 3}, {"_id": "a", "v": 1}, {"_id": "b", "v": 2}])
    result = execute_command(db[name], {"find": name, "projection": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": "a"}, {"_id": "b"}, {"_id": "c"}],
        msg="default order should return documents in _id order",
    )


# Property [Filter Preserves _id Order]: find with a filter and no explicit sort
# returns matching documents in _id order on clustered collections.
@pytest.mark.collection_mgmt
def test_filter_preserves_id_order(collection):
    """Test find with filter returns _id order on clustered collection."""
    name = create_clustered(collection)
    db = collection.database
    db[name].insert_many(
        [{"_id": "d", "x": 1}, {"_id": "b", "x": 2}, {"_id": "c", "x": 1}, {"_id": "a", "x": 1}]
    )
    result = execute_command(
        db[name],
        {"find": name, "filter": {"x": 1}, "projection": {"_id": 1}},
    )
    assertSuccess(
        result,
        [{"_id": "a"}, {"_id": "c"}, {"_id": "d"}],
        msg="find with filter should return matching documents in _id order",
    )


# Property [Aggregate Preserves _id Order]: aggregate without $sort returns
# documents in _id order on clustered collections.
@pytest.mark.collection_mgmt
def test_aggregate_preserves_id_order(collection):
    """Test aggregate returns _id order on clustered collection."""
    name = create_clustered(collection)
    db = collection.database
    db[name].insert_many([{"_id": "c", "x": 1}, {"_id": "a", "x": 2}, {"_id": "b", "x": 3}])
    result = execute_command(
        db[name],
        {
            "aggregate": name,
            "pipeline": [{"$match": {"x": {"$gte": 1}}}, {"$project": {"_id": 1}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": "a"}, {"_id": "b"}, {"_id": "c"}],
        msg="aggregate without $sort should return documents in _id order",
    )
