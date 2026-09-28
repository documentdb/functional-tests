"""readConcern with find: command options, empty/non-existent collections, views, and getMore."""

from typing import Any, Dict, cast

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import CommandTestCase
from documentdb_tests.framework.assertions import assertProperties, assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import ViewCollection

INTERACTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_with_options_and_read_concern",
        docs=[{"_id": 1, "x": 3, "y": 9}, {"_id": 2, "x": 1, "y": 9}, {"_id": 3, "x": 2, "y": 9}],
        command={
            "filter": {},
            "sort": {"x": 1},
            "projection": {"x": 1, "_id": 1},
            "limit": 2,
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 2, "x": 1}, {"_id": 3, "x": 2}],
        msg="find with readConcern should not interfere with sort/projection/limit options.",
    ),
    CommandTestCase(
        "find_on_empty_collection",
        docs=[],
        command={"filter": {}, "readConcern": {"level": "local"}},
        expected=[],
        msg="find with readConcern on empty collection should return empty.",
    ),
    CommandTestCase(
        "find_on_nonexistent_collection",
        docs=None,
        command={"filter": {}, "readConcern": {"level": "local"}},
        expected=[],
        msg="find with readConcern on non-existent collection should return empty.",
    ),
    CommandTestCase(
        "find_on_view",
        target_collection=ViewCollection(options={"pipeline": [{"$match": {"x": {"$gte": 10}}}]}),
        docs=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}, {"_id": 3, "x": 5}],
        command={"filter": {}, "sort": {"_id": 1}, "readConcern": {"level": "local"}},
        expected=[{"_id": 1, "x": 10}, {"_id": 2, "x": 20}],
        msg="find with readConcern on view should return filtered view results.",
    ),
    CommandTestCase(
        "find_first_batch_with_batch_size",
        docs=[{"_id": i, "x": i} for i in range(10)],
        command={
            "filter": {},
            "batchSize": 3,
            "sort": {"_id": 1},
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 0, "x": 0}, {"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="first batch from find with readConcern should contain 3 documents.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INTERACTION_TESTS))
def test_read_concern_command_interaction(collection, test: CommandTestCase):
    """Test readConcern works with other command options, collection states, and views."""
    collection = test.prepare(collection.database, collection)
    find_body = cast(Dict[str, Any], test.command)
    result = execute_command(collection, {"find": collection.name, **find_body})
    assertResult(result, expected=test.expected, msg=test.msg)


def test_getmore_after_find_with_read_concern_next_batch(collection):
    """Test getMore after find with readConcern returns next batch correctly."""
    collection.insert_many([{"_id": i, "x": i} for i in range(10)])

    initial_result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "batchSize": 3,
            "sort": {"_id": 1},
            "readConcern": {"level": "local"},
        },
    )
    cursor_id = initial_result["cursor"]["id"]

    getmore_result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 3},
    )
    expected_next = [{"_id": 3, "x": 3}, {"_id": 4, "x": 4}, {"_id": 5, "x": 5}]
    assertProperties(
        getmore_result,
        {"cursor.nextBatch": Eq(expected_next), "ok": Eq(1.0)},
        raw_res=True,
        msg="getMore after readConcern find should return next batch correctly.",
    )


def test_getmore_ignores_read_concern_parameter(collection):
    """Test getMore ignores a readConcern parameter and still returns the next batch."""
    collection.insert_many([{"_id": i, "x": i} for i in range(10)])

    initial_result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "batchSize": 3,
            "sort": {"_id": 1},
            "readConcern": {"level": "local"},
        },
    )
    cursor_id = initial_result["cursor"]["id"]

    getmore_result = execute_command(
        collection,
        {
            "getMore": cursor_id,
            "collection": collection.name,
            "batchSize": 3,
            "readConcern": {"level": "local"},
        },
    )
    expected_next = [{"_id": 3, "x": 3}, {"_id": 4, "x": 4}, {"_id": 5, "x": 5}]
    assertProperties(
        getmore_result,
        {"cursor.nextBatch": Eq(expected_next), "ok": Eq(1.0)},
        raw_res=True,
        msg="getMore should ignore a readConcern parameter and return the next batch.",
    )
