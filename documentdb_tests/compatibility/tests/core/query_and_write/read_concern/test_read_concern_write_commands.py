"""
readConcern on write commands outside transactions.

Verifies the behavior when readConcern is specified on write commands
(insert, update, delete, findAndModify) outside of a multi-document transaction.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Write Command Acceptance]: write commands accept readConcern outside transactions.
WRITE_COMMAND_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "insert_with_read_concern",
        command=lambda ctx: {
            "insert": ctx.collection,
            "documents": [{"_id": 1, "x": 1}],
            "readConcern": {"level": "local"},
        },
        expected={"n": 1, "ok": 1.0},
        msg="insert should accept readConcern outside transaction.",
    ),
    CommandTestCase(
        "update_with_read_concern",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 2}}}],
            "readConcern": {"level": "local"},
        },
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="update should accept readConcern outside transaction.",
    ),
    CommandTestCase(
        "delete_with_read_concern",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": 1}, "limit": 1}],
            "readConcern": {"level": "local"},
        },
        expected={"n": 1, "ok": 1.0},
        msg="delete should accept readConcern outside transaction.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WRITE_COMMAND_TESTS))
def test_write_command_with_read_concern(collection, test: CommandTestCase):
    """Test write commands accept readConcern outside transaction."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, expected=test.build_expected(ctx), msg=test.msg, raw_res=True)


def test_find_and_modify_with_read_concern_outside_transaction(collection):
    """Test findAndModify with readConcern outside transaction."""
    collection.insert_many([{"_id": 1, "x": 1}])
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$set": {"x": 2}},
            "readConcern": {"level": "local"},
        },
    )
    assertSuccessPartial(
        result,
        {"value": {"_id": 1, "x": 1}, "ok": 1.0},
        msg="findAndModify should accept readConcern outside transaction.",
    )
