"""Tests for validate command error cases.

Validates that validate returns expected errors for non-existent collections,
views, invalid option combinations, and truthy background values on standalone.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ERROR,
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    INVALID_OPTIONS_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

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


OPTION_ERROR_TESTS = INVALID_COMBINATION_TESTS + TRUTHY_TYPE_TESTS


@pytest.mark.parametrize("test", pytest_params(OPTION_ERROR_TESTS))
def test_validate_option_errors(collection, test):
    """Test that validate errors on invalid option combinations and truthy background."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"validate": collection.name, **test.command})
    assertFailureCode(result, test.error_code, msg=test.msg)
