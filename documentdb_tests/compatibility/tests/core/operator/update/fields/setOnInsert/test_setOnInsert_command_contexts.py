"""
Tests for $setOnInsert update operator - command contexts.

Covers updateOne and updateMany with upsert.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SETONINSERT_COMMAND_CONTEXT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="updateOne_upsert",
        query={"_id": 1},
        update={"$setOnInsert": {"x": 1}},
        upsert=True,
        expected={"n": 1, "nModified": 0, "ok": 1.0, "upserted": [{"index": 0, "_id": 1}]},
        msg="updateOne with $setOnInsert upsert should insert one doc",
    ),
    UpdateTestCase(
        id="updateMany_upsert",
        query={"status": "new"},
        update={"$setOnInsert": {"x": 1}},
        upsert=True,
        multi=True,
        expected={"n": 1, "nModified": 0, "ok": 1.0},
        msg="updateMany upsert should insert one doc",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETONINSERT_COMMAND_CONTEXT_TESTS))
def test_setOnInsert_command_contexts(collection, test):
    """Test $setOnInsert in various update command contexts."""
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": test.query,
                    "u": test.update,
                    "upsert": test.upsert,
                    "multi": test.multi,
                }
            ],
        },
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)


def test_setOnInsert_multi_existing_matches_noop(collection):
    """Test $setOnInsert is a no-op with multi:true + upsert when docs already match."""
    collection.insert_many([{"_id": 1, "k": 1, "a": "orig1"}, {"_id": 2, "k": 1, "a": "orig2"}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"k": 1},
                    "u": {"$setOnInsert": {"x": 99}},
                    "upsert": True,
                    "multi": True,
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"k": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "k": 1, "a": "orig1"}, {"_id": 2, "k": 1, "a": "orig2"}],
        msg="$setOnInsert fields should NOT be added to existing matched docs",
    )
