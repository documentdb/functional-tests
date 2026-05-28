"""Tests for index behavior on clustered collections."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult, assertSuccess, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    CLUSTERED_INDEX_DROP_ERROR,
    CLUSTERED_INDEX_HIDE_ERROR,
)
from documentdb_tests.framework.executor import execute_command

from .utils.clustered_utils import create_clustered


# Property [Cannot Drop Clustered Index by Name]: attempting to drop the
# clustered index by name produces the clustered index drop error.
@pytest.mark.collection_mgmt
def test_cannot_drop_clustered_by_name(collection):
    """Test dropping clustered index by name fails."""
    name = create_clustered(collection)
    result = execute_command(collection, {"dropIndexes": name, "index": "_id_"})
    assertResult(
        result,
        error_code=CLUSTERED_INDEX_DROP_ERROR,
        msg="should reject dropping clustered index by name",
    )


# Property [Cannot Drop Clustered Index by Key]: attempting to drop the
# clustered index by key pattern produces the clustered index drop error.
@pytest.mark.collection_mgmt
def test_cannot_drop_clustered_by_key(collection):
    """Test dropping clustered index by key pattern fails."""
    name = create_clustered(collection)
    result = execute_command(collection, {"dropIndexes": name, "index": {"_id": 1}})
    assertResult(
        result,
        error_code=CLUSTERED_INDEX_DROP_ERROR,
        msg="should reject dropping clustered index by key",
    )


# Property [dropIndexes Star Preserves Clustered]: dropIndexes("*") drops only
# secondary indexes and preserves the clustered index.
@pytest.mark.collection_mgmt
def test_drop_indexes_star_preserves_clustered(collection):
    """Test dropIndexes * preserves clustered index."""
    name = create_clustered(collection)
    db = collection.database
    db[name].create_index([("x", 1)], name="x_1")
    execute_command(collection, {"dropIndexes": name, "index": "*"})
    result = execute_command(collection, {"listIndexes": name})
    assertSuccess(
        result,
        [{"v": 2, "key": {"_id": 1}, "name": "_id_", "unique": True, "clustered": True}],
        msg="dropIndexes * should preserve clustered index",
    )


# Property [Cannot Hide Clustered Index]: attempting to hide the clustered index
# via collMod produces the clustered index hide error.
@pytest.mark.collection_mgmt
def test_cannot_hide_clustered_index(collection):
    """Test hiding clustered index fails."""
    name = create_clustered(collection)
    result = execute_command(
        collection, {"collMod": name, "index": {"name": "_id_", "hidden": True}}
    )
    assertResult(
        result, error_code=CLUSTERED_INDEX_HIDE_ERROR, msg="should reject hiding clustered index"
    )


# Property [Cannot Unhide Clustered Index]: attempting to unhide the clustered
# index via collMod also produces the clustered index hide error.
@pytest.mark.collection_mgmt
def test_cannot_unhide_clustered_index(collection):
    """Test unhiding clustered index fails."""
    name = create_clustered(collection)
    result = execute_command(
        collection, {"collMod": name, "index": {"name": "_id_", "hidden": False}}
    )
    assertResult(
        result, error_code=CLUSTERED_INDEX_HIDE_ERROR, msg="should reject unhiding clustered index"
    )


# Property [Explicit _id Index No-Op]: creating a plain {_id: 1} index on a
# clustered collection is a no-op - the index count does not change.
@pytest.mark.collection_mgmt
def test_explicit_id_index_noop(collection):
    """Test creating {_id: 1} index is a no-op."""
    name = create_clustered(collection)
    result = execute_command(
        collection, {"createIndexes": name, "indexes": [{"key": {"_id": 1}, "name": "test_id"}]}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "numIndexesBefore": 0, "numIndexesAfter": 0},
        msg="creating {_id: 1} should be a no-op",
    )
