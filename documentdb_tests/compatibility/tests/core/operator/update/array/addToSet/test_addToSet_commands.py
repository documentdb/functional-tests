"""Tests for $addToSet update command integration.

Covers: updateOne, updateMany, findAndModify, upsert, multiple fields,
interaction with other operators, large arrays, multi-update batch.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import (
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

COMMAND_RESULT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "upsert_creates_doc",
        setup_docs=[],
        query={"_id": 99},
        update={"$addToSet": {"arr": 5}},
        upsert=True,
        expected={"_id": 99, "arr": [5]},
        msg="Upsert should create doc with array containing the value",
    ),
    UpdateTestCase(
        "upsert_with_each",
        setup_docs=[],
        query={"_id": 99},
        update={"$addToSet": {"arr": {"$each": [1, 2, 3]}}},
        upsert=True,
        expected={"_id": 99, "arr": [1, 2, 3]},
        msg="Upsert with $each should create doc with all values",
    ),
    UpdateTestCase(
        "multiple_fields",
        setup_docs=[{"_id": 1, "a": [1], "b": [10]}],
        query={"_id": 1},
        update={"$addToSet": {"a": 2, "b": 20}},
        expected={"_id": 1, "a": [1, 2], "b": [10, 20]},
        msg="Should update multiple fields independently",
    ),
    UpdateTestCase(
        "combined_with_set",
        setup_docs=[{"_id": 1, "arr": [1], "x": 0}],
        query={"_id": 1},
        update={"$addToSet": {"arr": 2}, "$set": {"x": 99}},
        expected={"_id": 1, "arr": [1, 2], "x": 99},
        msg="$addToSet and $set on different fields should both succeed",
    ),
    UpdateTestCase(
        "empty_operand_noop",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {}},
        expected={"_id": 1, "arr": [1, 2]},
        msg="Empty $addToSet should be no-op",
    ),
    UpdateTestCase(
        "large_array",
        setup_docs=[{"_id": 1, "arr": list(range(1000))}],
        query={"_id": 1},
        update={"$addToSet": {"arr": 1000}},
        expected={"_id": 1, "arr": list(range(1001))},
        msg="Should add to large array correctly",
    ),
    UpdateTestCase(
        "each_many_values",
        setup_docs=[{"_id": 1, "arr": [0]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": list(range(1, 101))}}},
        expected={"_id": 1, "arr": list(range(101))},
        msg="$each with 100 values should add all",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMMAND_RESULT_TESTS))
def test_addToSet_command_integration(collection, test: UpdateTestCase):
    """Test $addToSet update command produces expected document."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": test.query, "u": test.update, "upsert": test.upsert, "multi": test.multi}
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)


def test_addToSet_updateOne(collection):
    """Test $addToSet with updateOne returns correct nModified."""
    collection.insert_one({"_id": 1, "arr": [1]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"arr": 2}}}],
        },
    )
    assertSuccessPartial(
        result, {"n": 1, "nModified": 1, "ok": 1.0}, msg="updateOne should modify doc"
    )


def test_addToSet_updateMany(collection):
    """Test $addToSet with updateMany updates all matched docs."""
    collection.insert_many(
        [{"_id": 1, "arr": [1]}, {"_id": 2, "arr": [1, 2]}, {"_id": 3, "arr": [2]}]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$addToSet": {"arr": 2}}, "multi": True}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result,
        [{"_id": 1, "arr": [1, 2]}, {"_id": 2, "arr": [1, 2]}, {"_id": 3, "arr": [2]}],
        msg="updateMany should update each document independently",
    )


def test_addToSet_findAndModify(collection):
    """Test $addToSet with findAndModify returns the updated document."""
    collection.insert_one({"_id": 1, "arr": ["a"]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$addToSet": {"arr": "b"}},
            "new": True,
        },
    )
    assertSuccessPartial(
        result,
        {"value": {"_id": 1, "arr": ["a", "b"]}},
        msg="findAndModify should return updated doc",
    )


def test_addToSet_no_modify_when_dup(collection):
    """Test $addToSet returns nModified=0 when value already present."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"arr": 2}}}],
        },
    )
    assertSuccessPartial(
        result, {"n": 1, "nModified": 0, "ok": 1.0}, msg="Should not modify when dup exists"
    )


def test_addToSet_multi_update_batch(collection):
    """Test $addToSet with multiple updates in a single command."""
    collection.insert_many([{"_id": 1, "arr": [1]}, {"_id": 2, "arr": [10]}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$addToSet": {"arr": 2}}},
                {"q": {"_id": 2}, "u": {"$addToSet": {"arr": 20}}},
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 2, "nModified": 2, "ok": 1.0},
        msg="Multi-update batch should update both docs",
    )
