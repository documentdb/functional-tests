"""Tests for validate command error cases.

Validates that validate returns expected errors for non-string collection name
types, invalid string values, non-existent collections, views, invalid option
combinations, and truthy background values on standalone.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ERROR,
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    INVALID_NAMESPACE_ERROR,
    INVALID_OPTIONS_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Type Rejection]: validate rejects all non-string BSON types for the collection name.
INVALID_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "double",
        command={"validate": 1.0},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject double for collection name",
    ),
    DiagnosticTestCase(
        "int32",
        command={"validate": 1},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject int32 for collection name",
    ),
    DiagnosticTestCase(
        "int64",
        command={"validate": Int64(1)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject int64 for collection name",
    ),
    DiagnosticTestCase(
        "decimal128",
        command={"validate": Decimal128("1")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject Decimal128 for collection name",
    ),
    DiagnosticTestCase(
        "bool_true",
        command={"validate": True},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject bool true for collection name",
    ),
    DiagnosticTestCase(
        "bool_false",
        command={"validate": False},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject bool false for collection name",
    ),
    DiagnosticTestCase(
        "null",
        command={"validate": None},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject null for collection name",
    ),
    DiagnosticTestCase(
        "object",
        command={"validate": {"a": 1}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject object for collection name",
    ),
    DiagnosticTestCase(
        "empty_object",
        command={"validate": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject empty object for collection name",
    ),
    DiagnosticTestCase(
        "array",
        command={"validate": [1, 2]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject array for collection name",
    ),
    DiagnosticTestCase(
        "empty_array",
        command={"validate": []},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject empty array for collection name",
    ),
    DiagnosticTestCase(
        "binary",
        command={"validate": Binary(b"data")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject Binary for collection name",
    ),
    DiagnosticTestCase(
        "objectid",
        command={"validate": ObjectId()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject ObjectId for collection name",
    ),
    DiagnosticTestCase(
        "datetime",
        command={"validate": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject datetime for collection name",
    ),
    DiagnosticTestCase(
        "regex",
        command={"validate": Regex(".*")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject Regex for collection name",
    ),
    DiagnosticTestCase(
        "timestamp",
        command={"validate": Timestamp(0, 0)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject Timestamp for collection name",
    ),
    DiagnosticTestCase(
        "code",
        command={"validate": Code("function(){}")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject JavaScript Code for collection name",
    ),
    DiagnosticTestCase(
        "minkey",
        command={"validate": MinKey()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject MinKey for collection name",
    ),
    DiagnosticTestCase(
        "maxkey",
        command={"validate": MaxKey()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject MaxKey for collection name",
    ),
]


# Property [Invalid String Values]: validate rejects invalid string values for collection name.
INVALID_STRING_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "empty_string",
        command={"validate": ""},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="validate should reject empty string for collection name",
    ),
    DiagnosticTestCase(
        "dollar_prefix",
        command={"validate": "$invalid"},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="validate should return NamespaceNotFound for dollar-prefixed collection name",
    ),
]


INVALID_ARGUMENT_TESTS = INVALID_TYPE_TESTS + INVALID_STRING_TESTS


@pytest.mark.parametrize("test", pytest_params(INVALID_ARGUMENT_TESTS))
def test_validate_rejects_invalid_arguments(collection, test):
    """Test that validate rejects non-string types and invalid string values."""
    result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


# Property [Non-Existent Collection]: validate returns NamespaceNotFound for
# a collection that does not exist.
NON_EXISTENT_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "non_existent_collection",
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="validate should return NamespaceNotFound for a non-existent collection",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NON_EXISTENT_TESTS))
def test_validate_non_existent(collection, test):
    """Test validate on non-existent collections returns expected error."""
    result = execute_command(collection, {"validate": f"{collection.name}_nonexistent_xyz"})
    assertFailureCode(result, test.error_code, msg=test.msg)


# Property [View Rejection]: validate rejects views.
def test_validate_view_rejected(database_client, collection):
    """Test validate on a view returns CommandNotSupportedOnView error."""
    source_name = f"{collection.name}_view_source"
    view_name = f"{collection.name}_view"
    database_client.create_collection(source_name)
    database_client[source_name].insert_one({"_id": 1})
    database_client.command("create", view_name, viewOn=source_name, pipeline=[])
    coll = database_client[view_name]
    result = execute_command(coll, {"validate": coll.name})
    assertFailureCode(
        result,
        COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="validate should reject views",
    )


# Property [Invalid Combinations]: validate rejects incompatible option combinations.
INVALID_COMBINATION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "metadata_with_full",
        command={"metadata": True, "full": True},
        error_code=INVALID_OPTIONS_ERROR,
        msg="validate should error with metadata: true and full: true",
    ),
    DiagnosticTestCase(
        "metadata_with_repair",
        command={"metadata": True, "repair": True, "fixMultikey": True},
        error_code=INVALID_OPTIONS_ERROR,
        msg="validate should error with metadata: true and repair: true",
    ),
    DiagnosticTestCase(
        "metadata_with_checkBSONConformance",
        command={"metadata": True, "checkBSONConformance": True},
        error_code=INVALID_OPTIONS_ERROR,
        msg="validate should error with metadata: true and checkBSONConformance: true",
    ),
    DiagnosticTestCase(
        "checkBSONConformance_with_repair",
        command={"checkBSONConformance": True, "repair": True, "fixMultikey": True},
        error_code=INVALID_OPTIONS_ERROR,
        msg="validate should error with checkBSONConformance: true and repair: true",
    ),
    DiagnosticTestCase(
        "metadata_with_background",
        command={"metadata": True, "background": True},
        error_code=INVALID_OPTIONS_ERROR,
        msg="validate should error with metadata: true and background: true",
    ),
]


# Property [Truthy Standalone Error]: validate rejects truthy background
# values on standalone mode.
TRUTHY_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "bool_true",
        command={"background": True},
        error_code=COMMAND_NOT_SUPPORTED_ERROR,
        msg="background: true not supported on standalone",
    ),
    DiagnosticTestCase(
        "int32_1",
        command={"background": 1},
        error_code=COMMAND_NOT_SUPPORTED_ERROR,
        msg="background: int 1 (truthy) not supported on standalone",
    ),
    DiagnosticTestCase(
        "string",
        command={"background": "true"},
        error_code=COMMAND_NOT_SUPPORTED_ERROR,
        msg="background: string (truthy) not supported on standalone",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_COMBINATION_TESTS))
def test_validate_option_errors(collection, test):
    """Test that validate errors on invalid option combinations."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"validate": collection.name, **test.command})
    assertFailureCode(result, test.error_code, msg=test.msg)


@pytest.mark.requires(validate_repair=True)
@pytest.mark.parametrize("test", pytest_params(TRUTHY_TYPE_TESTS))
def test_validate_background_truthy_rejected(collection, test):
    """Test that validate rejects truthy background values on standalone."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"validate": collection.name, **test.command})
    assertFailureCode(result, test.error_code, msg=test.msg)
