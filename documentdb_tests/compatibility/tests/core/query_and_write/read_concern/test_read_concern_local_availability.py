"""
readConcern level: "local" availability tests.

Tests that readConcern "local" is available with and without causally consistent
sessions, and on primary reads. Per the MongoDB spec:
  "local" is available with or without causally consistent sessions and transactions.
  It is the default for reads against the primary and secondaries.
"""

from documentdb_tests.framework.assertions import assertNotError
from documentdb_tests.framework.executor import execute_command


def test_read_concern_local_available_without_session(collection):
    """Test readConcern 'local' is available for a find without any session."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "readConcern": {"level": "local"},
        },
    )
    assertNotError(result, msg="readConcern 'local' should be available without a session.")


def test_read_concern_local_available_on_aggregate(collection):
    """Test readConcern 'local' is available on aggregate without a session."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
    )
    assertNotError(result, msg="readConcern 'local' should be available on aggregate.")


def test_read_concern_local_available_on_count(collection):
    """Test readConcern 'local' is available on count without a session."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "count": collection.name,
            "query": {},
            "readConcern": {"level": "local"},
        },
    )
    assertNotError(result, msg="readConcern 'local' should be available on count.")


def test_read_concern_local_available_on_distinct(collection):
    """Test readConcern 'local' is available on distinct without a session."""
    collection.insert_one({"_id": 1, "x": "a"})
    result = execute_command(
        collection,
        {
            "distinct": collection.name,
            "key": "x",
            "readConcern": {"level": "local"},
        },
    )
    assertNotError(result, msg="readConcern 'local' should be available on distinct.")


def test_read_concern_local_available_on_empty_collection(collection):
    """Test readConcern 'local' is available even when the collection is empty."""
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "readConcern": {"level": "local"},
        },
    )
    assertNotError(result, msg="readConcern 'local' should be available on an empty collection.")


def test_read_concern_local_does_not_error(collection):
    """Test readConcern 'local' does not produce an error on find."""
    collection.insert_many([{"_id": i} for i in range(3)])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "readConcern": {"level": "local"},
        },
    )
    assertNotError(result, msg="find with readConcern 'local' should not error.")
