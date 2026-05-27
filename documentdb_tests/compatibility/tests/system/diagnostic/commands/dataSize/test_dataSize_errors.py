"""Tests for dataSize command error conditions.

Covers namespace format errors (empty string, missing dot), unrecognized
command fields, and unsupported collection types (views).
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticErrorTest,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    INVALID_NAMESPACE_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


ERROR_TESTS: list[DiagnosticErrorTest] = [
    DiagnosticErrorTest(
        "empty_string",
        command={"dataSize": ""},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Empty string should fail",
    ),
    DiagnosticErrorTest(
        "no_dot",
        command={"dataSize": "nodot"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="No dot in namespace should fail",
    ),
    DiagnosticErrorTest(
        "unrecognized_field",
        command={"foo": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized field should error",
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
