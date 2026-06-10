"""Tests for killSessions command field type, Stable API, and response structure errors."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertResult
from documentdb_tests.framework.error_codes import (
    API_VERSION_REQUIRED_ERROR,
    API_STRICT_ERROR,
    API_VERSION_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, IsType

pytestmark = pytest.mark.no_parallel

# Property [Command Field Type Rejection]: the killSessions command field
# expects an array. All non-array BSON types are rejected.
KILLSESSIONS_FIELD_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"field_type_{tid}",
        command=lambda ctx, v=val: {"killSessions": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killSessions should reject {tid} as command field value",
    )
    for tid, val in [
        ("int32", 1),
        ("int32_zero", 0),
        ("int32_negative", -1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("double_zero", 0.0),
        ("double_negative", -1.0),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("string", "test"),
        ("string_empty", ""),
        ("object_empty", {}),
        ("object", {"key": "value"}),
        ("binary", Binary(b"\x00\x01\x02")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*", "i")),
        ("timestamp", Timestamp(1, 1)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("double_nan", float("nan")),
        ("double_inf", float("inf")),
    ]
] + [
    # Null produces a missing field error rather than a type mismatch.
    CommandTestCase(
        "field_type_null",
        command=lambda ctx: {"killSessions": None},
        error_code=MISSING_FIELD_ERROR,
        msg="killSessions should reject null as command field value",
    ),
]

# Property [Stable API V1 Rejection]: killSessions is NOT in API
# Version 1, so apiStrict true rejects it.
KILLSESSIONS_STABLE_API_STRICT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "api_strict_true",
        command={"killSessions": [], "apiVersion": "1", "apiStrict": True},
        error_code=API_STRICT_ERROR,
        msg="killSessions should be rejected with apiStrict true",
    ),
]

# Property [API Version Errors]: invalid apiVersion values and
# missing apiVersion with other API parameters are rejected.
KILLSESSIONS_API_VERSION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "api_version_2",
        command={"killSessions": [], "apiVersion": "2"},
        error_code=API_VERSION_ERROR,
        msg="killSessions should reject apiVersion 2",
    ),
    CommandTestCase(
        "api_version_empty",
        command={"killSessions": [], "apiVersion": ""},
        error_code=API_VERSION_ERROR,
        msg="killSessions should reject empty apiVersion",
    ),
    CommandTestCase(
        "api_strict_without_version",
        command={"killSessions": [], "apiStrict": True},
        error_code=API_VERSION_REQUIRED_ERROR,
        msg="killSessions should reject apiStrict without apiVersion",
    ),
    CommandTestCase(
        "api_deprecation_without_version",
        command={"killSessions": [], "apiDeprecationErrors": True},
        error_code=API_VERSION_REQUIRED_ERROR,
        msg="killSessions should reject apiDeprecationErrors without apiVersion",
    ),
]

KILLSESSIONS_FIELD_TYPE_AND_API_ERROR_TESTS: list[CommandTestCase] = (
    KILLSESSIONS_FIELD_TYPE_ERROR_TESTS
    + KILLSESSIONS_STABLE_API_STRICT_ERROR_TESTS
    + KILLSESSIONS_API_VERSION_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLSESSIONS_FIELD_TYPE_AND_API_ERROR_TESTS))
def test_killSessions_field_type_error(collection, test):
    """Test killSessions command field type and Stable API errors."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [Error Response Structure]: a failed killSessions response
# contains ok: 0.0, code (int), errmsg (string), and codeName (string).
def test_killSessions_error_response_structure(collection):
    """Test killSessions error response contains ok, code, errmsg, codeName."""
    result = execute_command(collection, {"killSessions": 1})
    details = getattr(result, "details", {})
    assertProperties(
        details,
        {
            "ok": Eq(0.0),
            "code": IsType("int"),
            "errmsg": IsType("string"),
            "codeName": IsType("string"),
        },
        msg="Error response should contain ok, code, errmsg, codeName",
        raw_res=True,
    )
