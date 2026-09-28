"""Tests for find command options: showRecordId, comment, noCursorTimeout, collation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Exists, IsType

# Property [Option Acceptance]: find accepts cross-cutting options (comment,
# noCursorTimeout, allowDiskUse, collation, readConcern) without affecting results.
FIND_OPTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "comment_string",
        docs=[{"_id": 1, "a": 10}],
        command=lambda ctx: {"find": ctx.collection, "comment": "test comment"},
        expected=[{"_id": 1, "a": 10}],
        msg="find should accept string comment without affecting results.",
    ),
    CommandTestCase(
        "comment_document",
        docs=[{"_id": 1, "a": 10}],
        command=lambda ctx: {
            "find": ctx.collection,
            "comment": {"purpose": "test", "version": 2},
        },
        expected=[{"_id": 1, "a": 10}],
        msg="find should accept document comment without affecting results.",
    ),
    CommandTestCase(
        "no_cursor_timeout_true",
        docs=[{"_id": 1, "a": 10}],
        command=lambda ctx: {"find": ctx.collection, "noCursorTimeout": True},
        expected=[{"_id": 1, "a": 10}],
        msg="find should accept noCursorTimeout=true.",
    ),
    CommandTestCase(
        "allow_disk_use_true",
        docs=[{"_id": 1, "a": 10}],
        command=lambda ctx: {"find": ctx.collection, "allowDiskUse": True},
        expected=[{"_id": 1, "a": 10}],
        msg="find should accept allowDiskUse=true.",
    ),
    CommandTestCase(
        "allow_disk_use_false",
        docs=[{"_id": 1, "a": 10}],
        command=lambda ctx: {"find": ctx.collection, "allowDiskUse": False},
        expected=[{"_id": 1, "a": 10}],
        msg="find should accept allowDiskUse=false.",
    ),
    CommandTestCase(
        "collation_acceptance",
        docs=[{"_id": 1, "name": "Alice"}],
        command=lambda ctx: {
            "find": ctx.collection,
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "name": "Alice"}],
        msg="find should accept valid collation document.",
    ),
    CommandTestCase(
        "read_concern_local",
        docs=[{"_id": 1, "a": 10}],
        command=lambda ctx: {
            "find": ctx.collection,
            "readConcern": {"level": "local"},
        },
        expected=[{"_id": 1, "a": 10}],
        msg="find should accept readConcern level local.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_OPTION_TESTS))
def test_find_options(database_client, collection, test):
    """Test find command option acceptance."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )


def test_find_show_record_id(collection):
    """Test find with showRecordId=true adds $recordId field."""
    collection.insert_many([{"_id": 1, "a": 10}])
    result = execute_command(collection, {"find": collection.name, "showRecordId": True})
    assertProperties(
        result,
        {"cursor.firstBatch.0.$recordId": Exists()},
        raw_res=True,
        msg="find should add $recordId field when showRecordId=true.",
    )


def test_find_show_record_id_type(collection):
    """Test find showRecordId returns Int64 value."""
    collection.insert_many([{"_id": 1, "a": 10}])
    result = execute_command(collection, {"find": collection.name, "showRecordId": True})
    assertResult(
        result,
        expected={"cursor.firstBatch.0.$recordId": IsType("long")},
        raw_res=True,
        msg="find should return $recordId as Int64.",
    )
