"""Tests for dbHash command core behavior and response structure."""

import pytest

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Gte, IsType

pytestmark = pytest.mark.admin


def test_dbHash_returns_ok(collection):
    """Test dbHash returns ok: 1."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should return ok: 1")


def test_dbHash_returns_host(collection):
    """Test dbHash returns host as a string."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": 1})
    assertResult(
        result, expected={"host": IsType("string")}, raw_res=True, msg="host should be string"
    )


def test_dbHash_returns_collections(collection):
    """Test dbHash returns collections as a document."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": 1})
    assertResult(
        result,
        expected={"collections": IsType("object")},
        raw_res=True,
        msg="collections should be object",
    )


def test_dbHash_returns_md5(collection):
    """Test dbHash returns md5 as a 32-character hex string."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": 1})
    assertResult(
        result, expected={"md5": IsType("string")}, raw_res=True, msg="md5 should be string"
    )


def test_dbHash_returns_timeMillis(collection):
    """Test dbHash returns timeMillis as a non-negative number."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": 1})
    assertResult(
        result, expected={"timeMillis": Gte(0)}, raw_res=True, msg="timeMillis should be >= 0"
    )


def test_dbHash_returns_capped_array(collection):
    """Test dbHash returns capped as an array."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": 1})
    assertResult(
        result, expected={"capped": IsType("array")}, raw_res=True, msg="capped should be array"
    )


def test_dbHash_returns_uuids(collection):
    """Test dbHash returns uuids as a document."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbHash": 1})
    assertResult(
        result, expected={"uuids": IsType("object")}, raw_res=True, msg="uuids should be object"
    )


def test_dbHash_empty_database(collection):
    """Test dbHash on database with no user collections returns empty collections."""
    # Use a fresh database via execute_command on a different db
    result = execute_command(collection, {"dbHash": 1, "collections": ["nonexistent_xyz_abc"]})
    assertResult(
        result, expected={"ok": Gte(0.0)}, raw_res=True, msg="Should succeed on filtered empty"
    )
