"""Tests for validate command core behavior.

Validates basic functionality, counts, consistency across calls, comment parameter,
behavior on different collection types (capped, timeseries, clustered), and valid
option combinations.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
    bind_collection,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Core Behavior]: validate returns expected results for populated
# and empty collections and supports common parameters.
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
    DiagnosticTestCase(
        "unrecognized_field_ignored",
        setup=[{"insert": "", "documents": [{"_id": 1}]}],
        command={"unknownField": 1},
        checks={"ok": Eq(1.0), "valid": Eq(True)},
        msg="validate should ignore unrecognized fields and succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CORE_BEHAVIOR_TESTS))
def test_validate_core_behavior(collection, test):
    """Test validate core behavior with various collection states."""
    for cmd in test.setup:
        execute_command(collection, bind_collection(cmd, collection.name))
    cmd = {"validate": collection.name}
    if test.command:
        cmd.update(test.command)
    result = execute_command(collection, cmd)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


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


def test_validate_capped_collection(database_client, collection):
    """Test validate on a capped collection succeeds."""
    coll_name = f"{collection.name}_capped"
    database_client.create_collection(coll_name, capped=True, size=1_048_576)
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1, "x": 1})
    result = execute_command(coll, {"validate": coll.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "valid": True},
        msg="validate should succeed on a capped collection",
    )


def test_validate_timeseries_collection(database_client, collection):
    """Test validate on a time series collection succeeds."""
    coll_name = f"{collection.name}_timeseries"
    database_client.create_collection(
        coll_name,
        timeseries={"timeField": "ts", "metaField": "meta"},
    )
    coll = database_client[coll_name]
    coll.insert_one({"ts": datetime(2024, 1, 1, tzinfo=timezone.utc), "meta": "a", "v": 1})
    result = execute_command(coll, {"validate": coll.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="validate should succeed on a timeseries collection",
    )


def test_validate_clustered_collection(database_client, collection):
    """Test validate on a clustered collection succeeds."""
    coll_name = f"{collection.name}_clustered"
    database_client.command(
        "create",
        coll_name,
        clusteredIndex={"key": {"_id": 1}, "unique": True},
    )
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1, "x": 1})
    result = execute_command(coll, {"validate": coll.name})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="validate should succeed on a clustered collection",
    )


# Property [Valid Options]: validate succeeds with each option individually
# and with compatible multi-option combinations.
VALID_OPTION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "all_options_false",
        command={"full": False, "repair": False, "metadata": False, "checkBSONConformance": False},
        checks={"ok": Eq(1.0)},
        msg="validate should succeed with all options set to false explicitly",
    ),
    DiagnosticTestCase(
        "full_true",
        command={"full": True},
        checks={"ok": Eq(1.0)},
        msg="validate with full: true should succeed",
    ),
    DiagnosticTestCase(
        "checkBSONConformance_true",
        command={"checkBSONConformance": True},
        checks={"ok": Eq(1.0)},
        msg="validate with checkBSONConformance: true should succeed",
    ),
    DiagnosticTestCase(
        "full_with_checkBSONConformance",
        command={"full": True, "checkBSONConformance": True},
        checks={"ok": Eq(1.0)},
        msg="validate with full: true and checkBSONConformance: true should succeed",
    ),
    DiagnosticTestCase(
        "metadata_true",
        command={"metadata": True},
        checks={"ok": Eq(1.0)},
        msg="validate with metadata: true should succeed",
    ),
]


# Property [Valid Repair Options]: validate succeeds with repair/fixMultikey
# options (standalone only).
VALID_REPAIR_OPTION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "fixMultikey_true",
        command={"fixMultikey": True},
        checks={"ok": Eq(1.0)},
        msg="validate with fixMultikey: true should succeed",
    ),
    DiagnosticTestCase(
        "repair_true",
        command={"repair": True},
        checks={"ok": Eq(1.0)},
        msg="validate with repair: true should succeed",
    ),
    DiagnosticTestCase(
        "repair_with_fixMultikey",
        command={"repair": True, "fixMultikey": True},
        checks={"ok": Eq(1.0)},
        msg="validate with repair: true and fixMultikey: true should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_OPTION_TESTS))
def test_validate_valid_options(collection, test):
    """Test that validate succeeds with valid option values."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"validate": collection.name, **test.command})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


@pytest.mark.requires(validate_repair=True)
@pytest.mark.parametrize("test", pytest_params(VALID_REPAIR_OPTION_TESTS))
def test_validate_valid_repair_options(collection, test):
    """Test that validate succeeds with repair/fixMultikey options on standalone."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"validate": collection.name, **test.command})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
