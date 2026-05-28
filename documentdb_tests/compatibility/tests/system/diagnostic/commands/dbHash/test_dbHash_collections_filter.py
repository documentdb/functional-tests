"""Tests for dbHash collections filter parameter."""

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Exists, NotExists

pytestmark = pytest.mark.admin


def test_dbHash_collections_empty_array(database_client):
    """Test dbHash with empty collections array returns all collections."""
    database_client["coll_a"].insert_one({"_id": 1})
    database_client["coll_b"].insert_one({"_id": 2})
    coll = database_client["coll_a"]
    result = execute_command(coll, {"dbHash": 1, "collections": []})
    assertResult(
        result,
        expected={"collections": {"coll_a": Exists(), "coll_b": Exists()}},
        raw_res=True,
        msg="Should include both",
    )


def test_dbHash_collections_specific(database_client):
    """Test dbHash with specific collection names returns only those hashes."""
    database_client["coll_a"].insert_one({"_id": 1})
    database_client["coll_b"].insert_one({"_id": 2})
    coll = database_client["coll_a"]
    result = execute_command(coll, {"dbHash": 1, "collections": ["coll_a"]})
    assertResult(
        result,
        expected={"collections": {"coll_a": Exists(), "coll_b": NotExists()}},
        raw_res=True,
        msg="Should only include coll_a",
    )


def test_dbHash_collections_nonexistent(collection):
    """Test dbHash with non-existent collection in array omits it from result."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": 1, "collections": ["nonexistent_xyz"]})
    assertResult(
        result,
        expected={"collections": {"nonexistent_xyz": NotExists()}},
        raw_res=True,
        msg="Non-existent should be omitted",
    )


def test_dbHash_collections_omitted(collection):
    """Test dbHash with omitted collections field returns all collections."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": 1})
    assertResult(
        result,
        expected={"collections": {collection.name: Exists()}},
        raw_res=True,
        msg="Should include test collection",
    )
