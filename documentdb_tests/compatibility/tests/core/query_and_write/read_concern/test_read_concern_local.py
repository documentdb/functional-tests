"""readConcern level 'local' availability and behavior with find."""

from typing import Any, Dict, cast

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import CommandTestCase
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params


def _update_status(coll):
    """Update _id 1's status to 'done' via a write command."""
    execute_command(
        coll,
        {"update": coll.name, "updates": [{"q": {"_id": 1}, "u": {"$set": {"status": "done"}}}]},
    )


def _delete_first(coll):
    """Delete _id 1 via a write command."""
    execute_command(coll, {"delete": coll.name, "deletes": [{"q": {"_id": 1}, "limit": 1}]})


# Each ``command`` is the find body (everything except the collection name); the
# test runner prepends ``"find": <resolved collection>``.
LOCAL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_omitted_read_concern_is_default",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command={"filter": {}, "sort": {"_id": 1}},
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="find without readConcern should return all documents (implicit default).",
    ),
    CommandTestCase(
        "find_local_without_session",
        docs=[{"_id": 1, "v": "a"}, {"_id": 2, "v": "b"}],
        command={"filter": {}, "sort": {"_id": 1}, "readConcern": {"level": "local"}},
        expected=[{"_id": 1, "v": "a"}, {"_id": 2, "v": "b"}],
        msg="find with readConcern 'local' must be available without a session or transaction.",
    ),
    CommandTestCase(
        "find_reads_fresh_data",
        docs=[{"_id": 1, "score": 100}],
        command={"filter": {"score": 100}, "readConcern": {"level": "local"}},
        expected=[{"_id": 1, "score": 100}],
        msg="find with readConcern 'local' should return inserted documents.",
    ),
    CommandTestCase(
        "find_sees_updated_document",
        docs=[{"_id": 1, "status": "pending"}],
        setup=_update_status,
        command={"filter": {"_id": 1}, "readConcern": {"level": "local"}},
        expected=[{"_id": 1, "status": "done"}],
        msg="find with readConcern 'local' must reflect an update applied to the local instance.",
    ),
    CommandTestCase(
        "find_reflects_delete",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        setup=_delete_first,
        command={"filter": {}, "sort": {"_id": 1}, "readConcern": {"level": "local"}},
        expected=[{"_id": 2}, {"_id": 3}],
        msg="find with readConcern 'local' must reflect a deletion applied to the local instance.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LOCAL_TESTS))
def test_read_concern_local(collection, test: CommandTestCase):
    """Test readConcern level 'local' availability and behavior."""
    collection = test.prepare(collection.database, collection)
    if test.setup:
        test.setup(collection)
    find_body = cast(Dict[str, Any], test.command)
    result = execute_command(collection, {"find": collection.name, **find_body})
    assertResult(result, expected=test.expected, msg=test.msg)
