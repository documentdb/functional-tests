"""Tests for profile command BSON type rejection.

Validates that non-numeric types for the profile, slowms, and sampleRate
fields are rejected with TYPE_MISMATCH_ERROR, and that null for the required
profile field produces MISSING_FIELD_ERROR.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Profile Type Rejection]: non-numeric types for the profile field
# are rejected with TYPE_MISMATCH_ERROR.
PROFILE_TYPE_REJECTION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "profile_bool_true",
        command={"profile": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject bool true",
    ),
    DiagnosticTestCase(
        "profile_bool_false",
        command={"profile": False},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject bool false",
    ),
    DiagnosticTestCase(
        "profile_string",
        command={"profile": "hello"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject string",
    ),
    DiagnosticTestCase(
        "profile_array",
        command={"profile": [1]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject array",
    ),
    DiagnosticTestCase(
        "profile_empty_array",
        command={"profile": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject empty array",
    ),
    DiagnosticTestCase(
        "profile_object",
        command={"profile": {"a": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject object",
    ),
    DiagnosticTestCase(
        "profile_empty_object",
        command={"profile": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject empty object",
    ),
    DiagnosticTestCase(
        "profile_objectid",
        command={"profile": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject ObjectId",
    ),
    DiagnosticTestCase(
        "profile_binary",
        command={"profile": Binary(b"")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject Binary",
    ),
    DiagnosticTestCase(
        "profile_regex",
        command={"profile": Regex("test")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject Regex",
    ),
    DiagnosticTestCase(
        "profile_timestamp",
        command={"profile": Timestamp(0, 0)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject Timestamp",
    ),
    DiagnosticTestCase(
        "profile_code",
        command={"profile": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject Code",
    ),
    DiagnosticTestCase(
        "profile_datetime",
        command={"profile": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject datetime",
    ),
    DiagnosticTestCase(
        "profile_minkey",
        command={"profile": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject MinKey",
    ),
    DiagnosticTestCase(
        "profile_maxkey",
        command={"profile": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="profile should reject MaxKey",
    ),
]

# Property [Profile Null Rejection]: null for the required profile field
# produces MISSING_FIELD_ERROR.
PROFILE_NULL_REJECTION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "profile_null",
        command={"profile": None},
        error_code=MISSING_FIELD_ERROR,
        msg="profile should reject null with missing field error",
    ),
]

# Property [slowms Type Rejection]: non-numeric types for the slowms field
# are rejected with TYPE_MISMATCH_ERROR.
SLOWMS_TYPE_REJECTION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "slowms_string",
        command={"profile": 0, "slowms": "hello"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="slowms should reject string",
    ),
    DiagnosticTestCase(
        "slowms_bool_true",
        command={"profile": 0, "slowms": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="slowms should reject bool true",
    ),
    DiagnosticTestCase(
        "slowms_bool_false",
        command={"profile": 0, "slowms": False},
        error_code=TYPE_MISMATCH_ERROR,
        msg="slowms should reject bool false",
    ),
    DiagnosticTestCase(
        "slowms_array",
        command={"profile": 0, "slowms": [1]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="slowms should reject array",
    ),
    DiagnosticTestCase(
        "slowms_object",
        command={"profile": 0, "slowms": {"a": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="slowms should reject object",
    ),
    DiagnosticTestCase(
        "slowms_objectid",
        command={"profile": 0, "slowms": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="slowms should reject ObjectId",
    ),
    DiagnosticTestCase(
        "slowms_regex",
        command={"profile": 0, "slowms": Regex("test")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="slowms should reject Regex",
    ),
    DiagnosticTestCase(
        "slowms_timestamp",
        command={"profile": 0, "slowms": Timestamp(0, 0)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="slowms should reject Timestamp",
    ),
    DiagnosticTestCase(
        "slowms_binary",
        command={"profile": 0, "slowms": Binary(b"")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="slowms should reject Binary",
    ),
    DiagnosticTestCase(
        "slowms_code",
        command={"profile": 0, "slowms": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="slowms should reject Code",
    ),
    DiagnosticTestCase(
        "slowms_minkey",
        command={"profile": 0, "slowms": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="slowms should reject MinKey",
    ),
    DiagnosticTestCase(
        "slowms_maxkey",
        command={"profile": 0, "slowms": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="slowms should reject MaxKey",
    ),
    DiagnosticTestCase(
        "slowms_datetime",
        command={"profile": 0, "slowms": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="slowms should reject datetime",
    ),
]

# Property [sampleRate Type Rejection]: non-numeric types for the sampleRate
# field are rejected with TYPE_MISMATCH_ERROR.
SAMPLERATE_TYPE_REJECTION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "samplerate_string",
        command={"profile": 0, "sampleRate": "hello"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="sampleRate should reject string",
    ),
    DiagnosticTestCase(
        "samplerate_bool_true",
        command={"profile": 0, "sampleRate": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="sampleRate should reject bool true",
    ),
    DiagnosticTestCase(
        "samplerate_bool_false",
        command={"profile": 0, "sampleRate": False},
        error_code=TYPE_MISMATCH_ERROR,
        msg="sampleRate should reject bool false",
    ),
    DiagnosticTestCase(
        "samplerate_array",
        command={"profile": 0, "sampleRate": [1]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="sampleRate should reject array",
    ),
    DiagnosticTestCase(
        "samplerate_object",
        command={"profile": 0, "sampleRate": {"a": 1}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="sampleRate should reject object",
    ),
    DiagnosticTestCase(
        "samplerate_objectid",
        command={"profile": 0, "sampleRate": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="sampleRate should reject ObjectId",
    ),
    DiagnosticTestCase(
        "samplerate_regex",
        command={"profile": 0, "sampleRate": Regex("test")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="sampleRate should reject Regex",
    ),
    DiagnosticTestCase(
        "samplerate_timestamp",
        command={"profile": 0, "sampleRate": Timestamp(0, 0)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="sampleRate should reject Timestamp",
    ),
    DiagnosticTestCase(
        "samplerate_binary",
        command={"profile": 0, "sampleRate": Binary(b"")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="sampleRate should reject Binary",
    ),
    DiagnosticTestCase(
        "samplerate_code",
        command={"profile": 0, "sampleRate": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="sampleRate should reject Code",
    ),
    DiagnosticTestCase(
        "samplerate_minkey",
        command={"profile": 0, "sampleRate": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="sampleRate should reject MinKey",
    ),
    DiagnosticTestCase(
        "samplerate_maxkey",
        command={"profile": 0, "sampleRate": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="sampleRate should reject MaxKey",
    ),
    DiagnosticTestCase(
        "samplerate_datetime",
        command={"profile": 0, "sampleRate": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="sampleRate should reject datetime",
    ),
]

PROFILE_TYPE_ERROR_TESTS = (
    PROFILE_TYPE_REJECTION_TESTS
    + PROFILE_NULL_REJECTION_TESTS
    + SLOWMS_TYPE_REJECTION_TESTS
    + SAMPLERATE_TYPE_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(PROFILE_TYPE_ERROR_TESTS))
def test_profile_type_errors(collection, test):
    """Test profile command rejects non-numeric types with correct error codes."""
    result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
