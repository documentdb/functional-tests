"""Tests for validate command core behavior.

Validates basic functionality, counts, consistency across calls, and comment parameter.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.error_codes import NAMESPACE_NOT_FOUND_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Core Behavior]: validate returns expected results for populated,
# empty, and non-existent collections and supports common parameters.
CORE_BEHAVIOR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "populated_collection",
        setup=[{"insert": "", "documents": [{"_id": i, "x": i} for i in range(5)]}],
        checks={"ok": Eq(1.0), "valid": Eq(True), "nrecords": Eq(5)},
        msg="validate should return valid: true with correct nrecords for a populated collection",
    ),
    DiagnosticTestCase(
        "empty_collection",
        setup=[{"create": ""}],
        checks={
            "ok": Eq(1.0),
            "valid": Eq(True),
            "nrecords": Eq(0),
            "nIndexes": Eq(1),
        },
        msg="validate should return nrecords: 0 and nIndexes: 1 for an empty collection",
    ),
    DiagnosticTestCase(
        "after_insert_and_delete_all",
        setup=[
            {"insert": "", "documents": [{"_id": i} for i in range(5)]},
            {"delete": "", "deletes": [{"q": {}, "limit": 0}]},
        ],
        checks={"ok": Eq(1.0), "valid": Eq(True), "nrecords": Eq(0)},
        msg="validate should return nrecords: 0 after deleting all documents",
    ),
    DiagnosticTestCase(
        "after_dropping_indexes",
        setup=[
            {"insert": "", "documents": [{"_id": 1, "x": 1}]},
            {"createIndexes": "", "indexes": [{"key": {"x": 1}, "name": "x_1"}]},
            {"dropIndexes": "", "index": "*"},
        ],
        checks={"ok": Eq(1.0), "nIndexes": Eq(1)},
        msg="validate should return nIndexes: 1 after dropping secondary indexes",
    ),
    DiagnosticTestCase(
        "with_comment",
        setup=[{"insert": "", "documents": [{"_id": 1}]}],
        command={"comment": "test comment"},
        checks={"ok": Eq(1.0)},
        msg="validate should succeed with comment parameter",
    ),
]

# Property [Non-Existent Collection]: validate returns NamespaceNotFound for
# a collection that does not exist.
NON_EXISTENT_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "non_existent_collection",
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="validate should return NamespaceNotFound for a non-existent collection",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CORE_BEHAVIOR_TESTS))
def test_validate_core_behavior(collection, test):
    """Test validate core behavior with various collection states."""
    for cmd in test.setup:
        execute_command(collection, {**cmd, next(iter(cmd)): collection.name})
    cmd = {"validate": collection.name}
    if test.command:
        cmd.update(test.command)
    result = execute_command(collection, cmd)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


@pytest.mark.parametrize("test", pytest_params(NON_EXISTENT_TESTS))
def test_validate_non_existent(collection, test):
    """Test validate on non-existent collections returns expected error."""
    result = execute_command(collection, {"validate": f"{collection.name}_nonexistent_xyz"})
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_validate_consistent_across_calls(collection):
    """Test validate returns consistent results across multiple calls."""
    collection.insert_many([{"_id": i, "x": i} for i in range(5)])
    result1 = execute_command(collection, {"validate": collection.name})
    result2 = execute_command(collection, {"validate": collection.name})
    assertProperties(
        result1,
        {
            "nrecords": Eq(result2["nrecords"]),
            "nIndexes": Eq(result2["nIndexes"]),
            "valid": Eq(result2["valid"]),
        },
        raw_res=True,
        msg="validate should return identical key fields across consecutive calls",
    )


def test_validate_reflects_modifications(collection):
    """Test validate reflects modifications between calls."""
    collection.insert_many([{"_id": i} for i in range(3)])
    execute_command(collection, {"validate": collection.name})
    collection.insert_many([{"_id": i} for i in range(3, 8)])
    result2 = execute_command(collection, {"validate": collection.name})
    assertProperties(
        result2,
        {"nrecords": Eq(8)},
        raw_res=True,
        msg="validate should reflect updated nrecords after additional inserts",
    )
