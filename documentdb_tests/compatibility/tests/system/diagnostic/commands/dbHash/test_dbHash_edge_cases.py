"""Tests for dbHash command edge cases."""

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Exists

pytestmark = pytest.mark.admin


def test_dbHash_special_characters_in_name(database_client):
    """Test dbHash with collection names containing special characters."""
    database_client.create_collection("coll-with-dash")
    database_client["coll-with-dash"].insert_one({"_id": 1})
    coll = database_client["coll-with-dash"]
    result = execute_command(coll, {"dbHash": 1})
    assertResult(
        result,
        expected={"collections": {"coll-with-dash": Exists()}},
        raw_res=True,
        msg="Special chars should work",
    )


def test_dbHash_many_collections(database_client):
    """Test dbHash with many collections includes all."""
    for i in range(10):
        database_client[f"multi_{i}"].insert_one({"_id": 1})
    coll = database_client["multi_0"]
    result = execute_command(coll, {"dbHash": 1})
    assertResult(
        result,
        expected={"collections": {"multi_0": Exists(), "multi_9": Exists()}},
        raw_res=True,
        msg="Should include all collections",
    )


def test_dbHash_only_capped_collections(database_client):
    """Test dbHash on database with only capped collections."""
    database_client.create_collection("only_capped", capped=True, size=4096)
    database_client["only_capped"].insert_one({"_id": 1})
    coll = database_client["only_capped"]
    result = execute_command(coll, {"dbHash": 1})
    assertResult(
        result,
        expected={"collections": {"only_capped": Exists()}},
        raw_res=True,
        msg="Should include capped-only db",
    )
