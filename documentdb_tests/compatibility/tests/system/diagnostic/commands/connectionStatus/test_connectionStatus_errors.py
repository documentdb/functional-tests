"""Tests for connectionStatus command error conditions.

Verifies that connectionStatus rejects invalid inputs with the correct error
codes. Covers unrecognized fields (UNRECOGNIZED_COMMAND_FIELD_ERROR) and
showPrivileges type-mismatch errors (TYPE_MISMATCH_ERROR) for all non-boolean,
non-numeric BSON types.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticErrorTest,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


ERROR_TESTS: list[DiagnosticErrorTest] = [
    DiagnosticErrorTest(
        id="unrecognized_field",
        command={"connectionStatus": 1, "foo": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized field should error",
    ),
    DiagnosticErrorTest(
        id="showPrivileges_string_type_mismatch",
        command={"connectionStatus": 1, "showPrivileges": "yes"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="showPrivileges string should be rejected as wrong type",
    ),
    DiagnosticErrorTest(
        id="showPrivileges_empty_string_type_mismatch",
        command={"connectionStatus": 1, "showPrivileges": ""},
        error_code=TYPE_MISMATCH_ERROR,
        msg="showPrivileges empty string should be rejected as wrong type",
    ),
    DiagnosticErrorTest(
        id="showPrivileges_string_false_type_mismatch",
        command={"connectionStatus": 1, "showPrivileges": "false"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="showPrivileges string 'false' should be rejected as wrong type",
    ),
    DiagnosticErrorTest(
        id="showPrivileges_array_type_mismatch",
        command={"connectionStatus": 1, "showPrivileges": [1]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="showPrivileges array should be rejected as wrong type",
    ),
    DiagnosticErrorTest(
        id="showPrivileges_object_type_mismatch",
        command={"connectionStatus": 1, "showPrivileges": {"a": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="showPrivileges object should be rejected as wrong type",
    ),
    DiagnosticErrorTest(
        id="showPrivileges_date_type_mismatch",
        command={
            "connectionStatus": 1,
            "showPrivileges": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="showPrivileges date should be rejected as wrong type",
    ),
    DiagnosticErrorTest(
        id="showPrivileges_objectId_type_mismatch",
        command={"connectionStatus": 1, "showPrivileges": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="showPrivileges objectId should be rejected as wrong type",
    ),
    DiagnosticErrorTest(
        id="showPrivileges_minKey_type_mismatch",
        command={"connectionStatus": 1, "showPrivileges": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="showPrivileges minKey should be rejected as wrong type",
    ),
    DiagnosticErrorTest(
        id="showPrivileges_maxKey_type_mismatch",
        command={"connectionStatus": 1, "showPrivileges": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="showPrivileges maxKey should be rejected as wrong type",
    ),
    DiagnosticErrorTest(
        id="showPrivileges_binData_type_mismatch",
        command={"connectionStatus": 1, "showPrivileges": Binary(b"")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="showPrivileges binData should be rejected as wrong type",
    ),
    DiagnosticErrorTest(
        id="showPrivileges_regex_type_mismatch",
        command={"connectionStatus": 1, "showPrivileges": Regex("test")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="showPrivileges regex should be rejected as wrong type",
    ),
    DiagnosticErrorTest(
        id="showPrivileges_timestamp_type_mismatch",
        command={"connectionStatus": 1, "showPrivileges": Timestamp(0, 0)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="showPrivileges timestamp should be rejected as wrong type",
    ),
    DiagnosticErrorTest(
        id="showPrivileges_code_type_mismatch",
        command={"connectionStatus": 1, "showPrivileges": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="showPrivileges code should be rejected as wrong type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_connectionStatus_error_conditions(collection, test):
    """Verify connectionStatus returns the expected error code for an invalid input."""
    if test.use_admin:
        result = execute_admin_command(collection, test.command)
    else:
        result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
