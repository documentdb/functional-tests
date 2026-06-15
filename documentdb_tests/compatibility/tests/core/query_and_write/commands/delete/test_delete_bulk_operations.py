"""Delete command bulk operations and ordered behavior.

Tests multiple delete statements, ordered vs unordered error handling.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertProperties,
    assertResult,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len

# Property [Bulk Summation]: n equals the sum of deletions across all statements.
BULK_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "multiple_statements_sum_n",
        docs=[{"_id": i, "a": i} for i in range(5)],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {"q": {"_id": 1}, "limit": 1},
                {"q": {"_id": 2}, "limit": 1},
            ],
        },
        expected={"ok": 1.0, "n": 2},
        msg="delete should sum n across multiple statements",
    ),
    CommandTestCase(
        "mixed_limits",
        docs=[{"_id": i, "status": "D" if i < 3 else "A"} for i in range(5)],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {"q": {"status": "D"}, "limit": 0},
                {"q": {"status": "A"}, "limit": 1},
            ],
        },
        expected={"ok": 1.0, "n": 4},
        msg="delete should handle mixed limit:0 and limit:1 in bulk",
    ),
    CommandTestCase(
        "duplicate_target_no_double_count",
        docs=[{"_id": 1}, {"_id": 2}],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {"q": {"_id": 1}, "limit": 1},
                {"q": {"_id": 1}, "limit": 1},
                {"q": {"_id": 2}, "limit": 1},
            ],
        },
        expected={"ok": 1.0, "n": 2},
        msg="delete should not count already-deleted document twice",
    ),
    CommandTestCase(
        "first_removes_docs_second_would_match",
        docs=[{"_id": i, "status": "D"} for i in range(3)],
        command=lambda ctx: {
            "delete": ctx.collection,
            "ordered": True,
            "deletes": [
                {"q": {"status": "D"}, "limit": 0},
                {"q": {"status": "D"}, "limit": 0},
            ],
        },
        expected={"ok": 1.0, "n": 3},
        msg="delete second statement should find nothing after first removed all",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BULK_TESTS))
def test_delete_bulk_operations(database_client, collection, test):
    """Test delete command bulk operations."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


def test_delete_ordered_true_stops_on_error(collection):
    """Test delete ordered:true stops execution after first error."""
    collection.insert_many([{"_id": i, "a": i} for i in range(5)])
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [
                {"q": {"_id": 1}, "limit": 1},
                {"q": {"$invalid": 1}, "limit": 1},
                {"q": {"_id": 3}, "limit": 1},
            ],
            "ordered": True,
        },
    )
    assertProperties(
        result,
        {
            "n": Eq(1),
            "writeErrors": [Len(1), Eq([{"index": 1, "code": BAD_VALUE_ERROR}])],
        },
        msg="delete ordered:true should stop at first error with exactly one writeError",
        raw_res=True,
    )


def test_delete_ordered_false_continues_on_error(collection):
    """Test delete ordered:false continues executing past errors."""
    collection.insert_many([{"_id": i, "a": i} for i in range(5)])
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [
                {"q": {"_id": 1}, "limit": 1},
                {"q": {"$invalid": 1}, "limit": 1},
                {"q": {"_id": 3}, "limit": 1},
            ],
            "ordered": False,
        },
    )
    assertProperties(
        result,
        {
            "n": Eq(2),
            "writeErrors": [Len(1), Eq([{"index": 1, "code": BAD_VALUE_ERROR}])],
        },
        msg="delete ordered:false should continue past errors and report exactly one writeError",
        raw_res=True,
    )


def test_delete_ordered_true_error_at_first(collection):
    """Test delete ordered:true with error in first statement returns n:0."""
    collection.insert_many([{"_id": i} for i in range(3)])
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [
                {"q": {"$invalid": 1}, "limit": 1},
                {"q": {"_id": 1}, "limit": 1},
            ],
            "ordered": True,
        },
    )
    assertProperties(
        result,
        {
            "n": Eq(0),
            "writeErrors": [Len(1), Eq([{"index": 0, "code": BAD_VALUE_ERROR}])],
        },
        msg="delete ordered:true should stop on first error with exactly one writeError",
        raw_res=True,
    )


def test_delete_ordered_false_error_at_first(collection):
    """Test delete ordered:false with error in first statement still executes subsequent."""
    collection.insert_many([{"_id": i} for i in range(3)])
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [
                {"q": {"$invalid": 1}, "limit": 1},
                {"q": {"_id": 1}, "limit": 1},
            ],
            "ordered": False,
        },
    )
    assertProperties(
        result,
        {
            "n": Eq(1),
            "writeErrors": [Len(1), Eq([{"index": 0, "code": BAD_VALUE_ERROR}])],
        },
        msg="delete ordered:false should continue past errors and report exactly one writeError",
        raw_res=True,
    )
