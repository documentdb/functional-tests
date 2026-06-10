"""Tests for killAllSessions readConcern field rejection."""

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
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    ILLEGAL_OPERATION_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.no_parallel

# Property [readConcern Type Rejection]: non-document readConcern values
# produce TYPE_MISMATCH_ERROR (14).
KILLALLSESSIONS_READCONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"readconcern_type_{tid}",
        command=lambda ctx, v=val: {"killAllSessions": [], "readConcern": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killAllSessions should reject {tid} readConcern",
    )
    for tid, val in [
        ("string", "local"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", []),
        ("array_nonempty", [1, 2]),
        ("binary", Binary(b"\x00\x01\x02")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [readConcern Level Rejection]: unsupported readConcern levels
# are rejected with INVALID_OPTIONS_ERROR (72).
KILLALLSESSIONS_READCONCERN_LEVEL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"readconcern_level_{tid}",
        command=lambda ctx, v=val: {
            "killAllSessions": [],
            "readConcern": {"level": v},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"killAllSessions should reject readConcern level {tid}",
    )
    for tid, val in [
        ("available", "available"),
        ("majority", "majority"),
        ("linearizable", "linearizable"),
        ("snapshot", "snapshot"),
    ]
]

# Property [readConcern Invalid Level]: invalid readConcern level strings
# are rejected with BAD_VALUE_ERROR (2).
KILLALLSESSIONS_READCONCERN_INVALID_LEVEL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"readconcern_invalid_level_{tid}",
        command=lambda ctx, v=val: {
            "killAllSessions": [],
            "readConcern": {"level": v},
        },
        error_code=BAD_VALUE_ERROR,
        msg=f"killAllSessions should reject invalid readConcern level {tid}",
    )
    for tid, val in [
        ("invalid_name", "invalid"),
        ("empty_string", ""),
    ]
]

# Property [readConcern Level Type Rejection]: non-string, non-null types
# for the readConcern level field are rejected with TYPE_MISMATCH_ERROR (14).
KILLALLSESSIONS_READCONCERN_LEVEL_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"readconcern_level_type_{tid}",
        command=lambda ctx, v=val: {
            "killAllSessions": [],
            "readConcern": {"level": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killAllSessions should reject {tid} type for readConcern level",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", ["local"]),
        ("document", {"a": 1}),
        ("binary", Binary(b"local")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("regex", Regex("local")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [readConcern Sub-field Validation]: unknown subfields and
# afterClusterTime are rejected.
KILLALLSESSIONS_READCONCERN_SUBFIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_unknown_subfield",
        command=lambda ctx: {
            "killAllSessions": [],
            "readConcern": {"bogusField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="killAllSessions should reject unknown subfield in readConcern",
    ),
    CommandTestCase(
        "readconcern_other_subfield",
        command=lambda ctx: {
            "killAllSessions": [],
            "readConcern": {"other": "val"},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="killAllSessions should reject unrecognized readConcern subfield",
    ),
    CommandTestCase(
        "readconcern_afterclustertime",
        command=lambda ctx: {
            "killAllSessions": [],
            "readConcern": {"afterClusterTime": Timestamp(1, 1)},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="killAllSessions should reject afterClusterTime in readConcern",
    ),
]

KILLALLSESSIONS_READCONCERN_ERROR_TESTS: list[CommandTestCase] = (
    KILLALLSESSIONS_READCONCERN_TYPE_ERROR_TESTS
    + KILLALLSESSIONS_READCONCERN_LEVEL_ERROR_TESTS
    + KILLALLSESSIONS_READCONCERN_INVALID_LEVEL_ERROR_TESTS
    + KILLALLSESSIONS_READCONCERN_LEVEL_TYPE_ERROR_TESTS
    + KILLALLSESSIONS_READCONCERN_SUBFIELD_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLALLSESSIONS_READCONCERN_ERROR_TESTS))
def test_killAllSessions_readconcern_errors(collection, test):
    """Test killAllSessions readConcern field rejection."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
