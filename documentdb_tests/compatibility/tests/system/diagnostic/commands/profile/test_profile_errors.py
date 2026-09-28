"""Tests for profile command validation error cases.

Validates sampleRate range rejection, filter value rejection, unrecognized
field rejection, and case-sensitive command name rejection.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    COMMAND_NOT_FOUND_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [sampleRate Range Rejection]: sampleRate values outside [0, 1]
# are rejected with BAD_VALUE_ERROR.
SAMPLERATE_RANGE_REJECTION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "samplerate_neg_0_1",
        command={"profile": 0, "sampleRate": -0.1},
        error_code=BAD_VALUE_ERROR,
        msg="sampleRate should reject -0.1",
    ),
    DiagnosticTestCase(
        "samplerate_1_1",
        command={"profile": 0, "sampleRate": 1.1},
        error_code=BAD_VALUE_ERROR,
        msg="sampleRate should reject 1.1",
    ),
    DiagnosticTestCase(
        "samplerate_2_0",
        command={"profile": 0, "sampleRate": 2.0},
        error_code=BAD_VALUE_ERROR,
        msg="sampleRate should reject 2.0",
    ),
    DiagnosticTestCase(
        "samplerate_neg_1_0",
        command={"profile": 0, "sampleRate": -1.0},
        error_code=BAD_VALUE_ERROR,
        msg="sampleRate should reject -1.0",
    ),
]

# Property [filter Type Rejection]: non-object, non-"unset" values for the
# filter field are rejected with BAD_VALUE_ERROR.
FILTER_REJECTION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "filter_string_UNSET",
        command={"profile": 1, "filter": "UNSET"},
        error_code=BAD_VALUE_ERROR,
        msg="filter should reject 'UNSET' (case-sensitive)",
    ),
    DiagnosticTestCase(
        "filter_string_Unset",
        command={"profile": 1, "filter": "Unset"},
        error_code=BAD_VALUE_ERROR,
        msg="filter should reject 'Unset' (case-sensitive)",
    ),
    DiagnosticTestCase(
        "filter_empty_string",
        command={"profile": 1, "filter": ""},
        error_code=BAD_VALUE_ERROR,
        msg="filter should reject empty string",
    ),
    DiagnosticTestCase(
        "filter_string_hello",
        command={"profile": 1, "filter": "hello"},
        error_code=BAD_VALUE_ERROR,
        msg="filter should reject arbitrary string",
    ),
    DiagnosticTestCase(
        "filter_int",
        command={"profile": 1, "filter": 1},
        error_code=BAD_VALUE_ERROR,
        msg="filter should reject int",
    ),
    DiagnosticTestCase(
        "filter_bool",
        command={"profile": 1, "filter": True},
        error_code=BAD_VALUE_ERROR,
        msg="filter should reject bool",
    ),
    DiagnosticTestCase(
        "filter_null",
        command={"profile": 1, "filter": None},
        error_code=BAD_VALUE_ERROR,
        msg="filter should reject null",
    ),
    DiagnosticTestCase(
        "filter_array",
        command={"profile": 1, "filter": []},
        error_code=BAD_VALUE_ERROR,
        msg="filter should reject array",
    ),
]

# Property [Unrecognized Fields]: unrecognized fields in the command document
# are rejected with UNRECOGNIZED_COMMAND_FIELD_ERROR.
UNRECOGNIZED_FIELD_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "unrecognized_unknownField",
        command={"profile": 0, "unknownField": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="profile should reject unrecognized field 'unknownField'",
    ),
    DiagnosticTestCase(
        "unrecognized_extraParam",
        command={"profile": 0, "extraParam": "value"},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="profile should reject unrecognized field 'extraParam'",
    ),
]

# Property [Case-Sensitive Command Name]: the command name is case-sensitive;
# mismatched case produces COMMAND_NOT_FOUND_ERROR.
CASE_SENSITIVITY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "case_Profile",
        command={"Profile": 0},
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="'Profile' (capital P) should not be recognized",
    ),
]

PROFILE_ERROR_TESTS = (
    SAMPLERATE_RANGE_REJECTION_TESTS
    + FILTER_REJECTION_TESTS
    + UNRECOGNIZED_FIELD_TESTS
    + CASE_SENSITIVITY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(PROFILE_ERROR_TESTS))
def test_profile_errors(collection, test):
    """Test profile command rejects invalid inputs with correct error codes."""
    result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
