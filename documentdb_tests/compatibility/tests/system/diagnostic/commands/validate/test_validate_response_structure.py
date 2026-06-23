"""Tests for validate command response structure.

Validates presence, types, and values of response fields for healthy collections,
including keysPerIndex/indexDetails structure and full/metadata mode responses.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, Gte, IsType, NotExists

# Property [Response Structure]: validate returns expected field types and values for
# healthy collections.
PROPERTY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "ok_is_1",
        checks={"ok": Eq(1.0)},
        msg="validate should return ok: 1.0",
    ),
    DiagnosticTestCase(
        "ns_is_string",
        checks={"ns": IsType("string")},
        msg="validate should return ns as a string",
    ),
    DiagnosticTestCase(
        "nInvalidDocuments_is_int",
        checks={"nInvalidDocuments": IsType("int")},
        msg="validate should return nInvalidDocuments as an int",
    ),
    DiagnosticTestCase(
        "nNonCompliantDocuments_is_int",
        checks={"nNonCompliantDocuments": IsType("int")},
        msg="validate should return nNonCompliantDocuments as an int",
    ),
    DiagnosticTestCase(
        "nrecords_is_int",
        checks={"nrecords": IsType("int")},
        msg="validate should return nrecords as an int",
    ),
    DiagnosticTestCase(
        "nIndexes_is_int",
        checks={"nIndexes": IsType("int")},
        msg="validate should return nIndexes as an int",
    ),
    DiagnosticTestCase(
        "keysPerIndex_is_object",
        checks={"keysPerIndex": IsType("object")},
        msg="validate should return keysPerIndex as an object",
    ),
    DiagnosticTestCase(
        "indexDetails_is_object",
        checks={"indexDetails": IsType("object")},
        msg="validate should return indexDetails as an object",
    ),
    DiagnosticTestCase(
        "valid_is_bool",
        checks={"valid": IsType("bool")},
        msg="validate should return valid as a bool",
    ),
    DiagnosticTestCase(
        "repaired_is_bool",
        checks={"repaired": IsType("bool")},
        msg="validate should return repaired as a bool",
    ),
    DiagnosticTestCase(
        "warnings_is_array",
        checks={"warnings": IsType("array")},
        msg="validate should return warnings as an array",
    ),
    DiagnosticTestCase(
        "errors_is_array",
        checks={"errors": IsType("array")},
        msg="validate should return errors as an array",
    ),
    DiagnosticTestCase(
        "extraIndexEntries_is_array",
        checks={"extraIndexEntries": IsType("array")},
        msg="validate should return extraIndexEntries as an array",
    ),
    DiagnosticTestCase(
        "missingIndexEntries_is_array",
        checks={"missingIndexEntries": IsType("array")},
        msg="validate should return missingIndexEntries as an array",
    ),
    DiagnosticTestCase(
        "corruptRecords_is_array",
        checks={"corruptRecords": IsType("array")},
        msg="validate should return corruptRecords as an array",
    ),
    DiagnosticTestCase(
        "uuid_exists",
        checks={"uuid": Exists()},
        msg="validate should return uuid field",
    ),
    DiagnosticTestCase(
        "nInvalidDocuments_zero_healthy",
        checks={"nInvalidDocuments": Eq(0)},
        msg="validate should return nInvalidDocuments: 0 for a healthy collection",
    ),
    DiagnosticTestCase(
        "nNonCompliantDocuments_zero_healthy",
        checks={"nNonCompliantDocuments": Eq(0)},
        msg="validate should return nNonCompliantDocuments: 0 for a healthy collection",
    ),
    DiagnosticTestCase(
        "valid_true_healthy",
        checks={"valid": Eq(True)},
        msg="validate should return valid: true for a healthy collection",
    ),
    DiagnosticTestCase(
        "warnings_empty_healthy",
        checks={"warnings": Eq([])},
        msg="validate should return empty warnings for a healthy collection",
    ),
    DiagnosticTestCase(
        "errors_empty_healthy",
        checks={"errors": Eq([])},
        msg="validate should return empty errors for a healthy collection",
    ),
    DiagnosticTestCase(
        "extraIndexEntries_empty_healthy",
        checks={"extraIndexEntries": Eq([])},
        msg="validate should return empty extraIndexEntries for a healthy collection",
    ),
    DiagnosticTestCase(
        "missingIndexEntries_empty_healthy",
        checks={"missingIndexEntries": Eq([])},
        msg="validate should return empty missingIndexEntries for a healthy collection",
    ),
    DiagnosticTestCase(
        "corruptRecords_empty_healthy",
        checks={"corruptRecords": Eq([])},
        msg="validate should return empty corruptRecords for a healthy collection",
    ),
    DiagnosticTestCase(
        "nIndexes_gte_1",
        checks={"nIndexes": Gte(1)},
        msg="validate should return nIndexes >= 1 (at least _id index)",
    ),
    DiagnosticTestCase(
        "repairMode_is_string",
        checks={"repairMode": IsType("string")},
        msg="validate should return repairMode as a string",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROPERTY_TESTS))
def test_validate_response_properties(collection, test):
    """Test validate response fields have expected types and values."""
    collection.insert_many([{"_id": i, "x": i} for i in range(5)])
    result = execute_command(collection, {"validate": collection.name})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


# Property [Response Values]: validate returns correct dynamic values matching
# collection state (nrecords, nIndexes, ns).
RESPONSE_VALUE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "nrecords_matches_count",
        setup=[
            {"insert": "", "documents": [{"_id": i} for i in range(10)]},
        ],
        checks={"nrecords": Eq(10)},
        msg="validate should return nrecords matching document count",
    ),
    DiagnosticTestCase(
        "nIndexes_with_secondary",
        setup=[
            {"insert": "", "documents": [{"_id": 1, "x": 1, "y": 1}]},
            {
                "createIndexes": "",
                "indexes": [
                    {"key": {"x": 1}, "name": "x_1"},
                    {"key": {"y": 1}, "name": "y_1"},
                ],
            },
        ],
        checks={"nIndexes": Eq(3)},
        msg="validate should return nIndexes: 3 with two secondary indexes",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_VALUE_TESTS))
def test_validate_response_values(collection, test):
    """Test validate response values match collection state."""
    for cmd in test.setup:
        execute_command(collection, {**cmd, next(iter(cmd)): collection.name})
    result = execute_command(collection, {"validate": collection.name})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_validate_ns_matches_namespace(collection):
    """Test validate ns field matches the actual database.collection namespace."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"validate": collection.name})
    expected_ns = f"{collection.database.name}.{collection.name}"
    assertSuccessPartial(
        result,
        {"ns": expected_ns},
        msg="validate should return ns matching the actual namespace",
    )


# Property [Detailed Structure]: validate returns correct sub-structure for
# keysPerIndex, indexDetails, and option-specific response shapes.
DETAILED_STRUCTURE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "keysPerIndex_entries",
        setup=[
            {"insert": "", "documents": [{"_id": i, "x": i} for i in range(5)]},
            {
                "createIndexes": "",
                "indexes": [{"key": {"x": 1}, "name": "x_1"}],
            },
        ],
        checks={
            "keysPerIndex._id_": IsType("int"),
            "keysPerIndex.x_1": IsType("int"),
        },
        msg="keysPerIndex should have integer entries for each index",
    ),
    DiagnosticTestCase(
        "indexDetails_entries",
        setup=[
            {"insert": "", "documents": [{"_id": i, "x": i} for i in range(5)]},
            {
                "createIndexes": "",
                "indexes": [{"key": {"x": 1}, "name": "x_1"}],
            },
        ],
        checks={
            "indexDetails._id_.valid": Eq(True),
            "indexDetails._id_.spec": IsType("object"),
            "indexDetails.x_1.valid": Eq(True),
            "indexDetails.x_1.spec": IsType("object"),
        },
        msg="indexDetails entries should have valid: true and spec as object",
    ),
    DiagnosticTestCase(
        "full_true_response",
        setup=[{"insert": "", "documents": [{"_id": 1}]}],
        command={"full": True},
        checks={
            "ok": Eq(1.0),
            "valid": Eq(True),
            "ns": IsType("string"),
            "nrecords": IsType("int"),
            "nIndexes": Gte(1),
            "keysPerIndex": IsType("object"),
            "indexDetails": IsType("object"),
            "repairMode": Eq("None"),
        },
        msg="validate with full: true should return all standard response fields",
    ),
    DiagnosticTestCase(
        "metadata_true_response",
        setup=[
            {"insert": "", "documents": [{"_id": i, "x": i} for i in range(5)]},
        ],
        command={"metadata": True},
        checks={
            "ok": Eq(1.0),
            "valid": Eq(True),
            "ns": IsType("string"),
            "nIndexes": IsType("int"),
            "nrecords": NotExists(),
            "nInvalidDocuments": NotExists(),
            "nNonCompliantDocuments": NotExists(),
        },
        msg="validate with metadata: true should return structural fields"
        " but omit document-count fields",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DETAILED_STRUCTURE_TESTS))
def test_validate_detailed_structure(collection, test):
    """Test validate response sub-structure for indexes and option modes."""
    for cmd in test.setup:
        execute_command(collection, {**cmd, next(iter(cmd)): collection.name})
    cmd = {"validate": collection.name}
    if test.command:
        cmd.update(test.command)
    result = execute_command(collection, cmd)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
