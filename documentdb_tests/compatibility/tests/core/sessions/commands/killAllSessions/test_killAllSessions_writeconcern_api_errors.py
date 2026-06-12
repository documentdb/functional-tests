"""Tests for killAllSessions writeConcern and Stable API rejection."""

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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    API_PARAMS_WITHOUT_VERSION_ERROR,
    API_STRICT_ERROR,
    API_VERSION_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.no_parallel

# Property [writeConcern Type Rejection]: non-document writeConcern values are rejected.
KILLALLSESSIONS_WRITECONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"writeconcern_type_{tid}",
        command=lambda ctx, v=val: {"killAllSessions": [], "writeConcern": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killAllSessions should reject {tid} writeConcern",
    )
    for tid, val in [
        ("string", "majority"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("array", []),
        ("array_nonempty", [1, 2]),
        ("binary", Binary(b"\x00\x01\x02")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*", "i")),
        ("timestamp", Timestamp(1, 1)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [writeConcern Document Rejection]: document writeConcern values are rejected.
KILLALLSESSIONS_WRITECONCERN_DOC_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"writeconcern_doc_{tid}",
        command=lambda ctx, v=val: {"killAllSessions": [], "writeConcern": v},
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"killAllSessions should reject writeConcern {tid}",
    )
    for tid, val in [
        ("empty", {}),
        ("w_1", {"w": 1}),
        ("w_majority", {"w": "majority"}),
        ("j_true", {"j": True}),
    ]
]

# Property [Stable API Rejection]: killAllSessions is rejected with
# apiStrict true or invalid apiVersion values.
KILLALLSESSIONS_API_STRICT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "api_strict_true",
        command=lambda ctx: {
            "killAllSessions": [],
            "apiVersion": "1",
            "apiStrict": True,
        },
        error_code=API_STRICT_ERROR,
        msg="killAllSessions should be rejected with apiStrict true",
    ),
]

# Property [API Version Rejection]: invalid apiVersion values are rejected.
KILLALLSESSIONS_API_VERSION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "api_version_2",
        command=lambda ctx: {"killAllSessions": [], "apiVersion": "2"},
        error_code=API_VERSION_ERROR,
        msg="killAllSessions should reject apiVersion 2",
    ),
    CommandTestCase(
        "api_version_empty",
        command=lambda ctx: {"killAllSessions": [], "apiVersion": ""},
        error_code=API_VERSION_ERROR,
        msg="killAllSessions should reject empty apiVersion",
    ),
]

# Property [apiStrict/apiDeprecationErrors without apiVersion]: specifying
# apiStrict or apiDeprecationErrors without apiVersion is rejected.
KILLALLSESSIONS_API_MISSING_VERSION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "api_strict_without_version",
        command=lambda ctx: {"killAllSessions": [], "apiStrict": True},
        error_code=API_PARAMS_WITHOUT_VERSION_ERROR,
        msg="killAllSessions should reject apiStrict without apiVersion",
    ),
    CommandTestCase(
        "api_deprecation_without_version",
        command=lambda ctx: {"killAllSessions": [], "apiDeprecationErrors": True},
        error_code=API_PARAMS_WITHOUT_VERSION_ERROR,
        msg="killAllSessions should reject apiDeprecationErrors without apiVersion",
    ),
]

KILLALLSESSIONS_WRITECONCERN_API_ERROR_TESTS: list[CommandTestCase] = (
    KILLALLSESSIONS_WRITECONCERN_TYPE_ERROR_TESTS
    + KILLALLSESSIONS_WRITECONCERN_DOC_ERROR_TESTS
    + KILLALLSESSIONS_API_STRICT_ERROR_TESTS
    + KILLALLSESSIONS_API_VERSION_ERROR_TESTS
    + KILLALLSESSIONS_API_MISSING_VERSION_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLALLSESSIONS_WRITECONCERN_API_ERROR_TESTS))
def test_killAllSessions_writeconcern_api_errors(collection, test):
    """Test killAllSessions writeConcern and Stable API rejection."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
