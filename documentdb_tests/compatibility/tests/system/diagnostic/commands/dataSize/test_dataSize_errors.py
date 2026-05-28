"""Tests for dataSize command error conditions.

Covers namespace format errors, unrecognized command fields, min/max
constraint violations, and unsupported collection types (views).
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    INVALID_NAMESPACE_ERROR,
    OPERATION_FAILED_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


ERROR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "empty_string",
        command={"dataSize": ""},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Empty string should fail",
    ),
    DiagnosticTestCase(
        "no_dot",
        command={"dataSize": "nodot"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="No dot in namespace should fail",
    ),
    DiagnosticTestCase(
        "unrecognized_field",
        command={"foo": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized field should error",
    ),
    DiagnosticTestCase(
        "min_max_without_keyPattern",
        command={"min": {"x": 0}, "max": {"x": 5}},
        error_code=OPERATION_FAILED_ERROR,
        msg="min/max without keyPattern should error",
    ),
    DiagnosticTestCase(
        "min_only",
        command={"keyPattern": {"_id": 1}, "min": {"_id": 5}},
        error_code=BAD_VALUE_ERROR,
        msg="min without max should error",
    ),
    DiagnosticTestCase(
        "max_only",
        command={"keyPattern": {"_id": 1}, "max": {"_id": 5}},
        error_code=BAD_VALUE_ERROR,
        msg="max without min should error",
    ),
    DiagnosticTestCase(
        "namespace_without_db_prefix",
        command={"dataSize": "just_collection_name"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Namespace without db prefix should error",
    ),
    DiagnosticTestCase(
        "min_set_max_null",
        command={"keyPattern": {"_id": 1}, "min": {"_id": 0}, "max": None},
        error_code=BAD_VALUE_ERROR,
        msg="min set with max null should error",
    ),
    DiagnosticTestCase(
        "min_null_max_set",
        command={"keyPattern": {"_id": 1}, "min": None, "max": {"_id": 5}},
        error_code=BAD_VALUE_ERROR,
        msg="max set with min null should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_dataSize_error(collection, test):
    """Test dataSize with invalid arguments returns expected errors."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    cmd = {"dataSize": ns, **(test.command or {})}
    result = execute_command(collection, cmd)
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_dataSize_view(database_client):
    """Test dataSize on a view returns error."""
    database_client.create_collection("base_ds")
    database_client.command("create", "ds_view", viewOn="base_ds", pipeline=[])
    ns = f"{database_client.name}.ds_view"
    coll = database_client["ds_view"]
    result = execute_command(coll, {"dataSize": ns})
    assertFailureCode(result, COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR, msg="View should error")
