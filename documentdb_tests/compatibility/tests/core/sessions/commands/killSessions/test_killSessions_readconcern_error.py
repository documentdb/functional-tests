"""Tests for killSessions readConcern field errors."""

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
    BAD_VALUE_ERROR,
    ILLEGAL_OPERATION_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.no_parallel

# Property [readConcern Level Rejection]: readConcern with levels other
# than "local" is rejected.
KILLSESSIONS_READCONCERN_LEVEL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_majority",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": {"level": "majority"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="killSessions should reject readConcern level majority",
    ),
    CommandTestCase(
        "readconcern_available",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": {"level": "available"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="killSessions should reject readConcern level available",
    ),
    CommandTestCase(
        "readconcern_linearizable",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": {"level": "linearizable"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="killSessions should reject readConcern level linearizable",
    ),
    CommandTestCase(
        "readconcern_snapshot",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": {"level": "snapshot"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="killSessions should reject readConcern level snapshot",
    ),
    CommandTestCase(
        "readconcern_level_invalid_name",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": {"level": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="killSessions should reject unrecognized readConcern level name",
    ),
    CommandTestCase(
        "readconcern_level_empty_string",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": {"level": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="killSessions should reject empty string readConcern level",
    ),
]

# Property [readConcern Type Rejection]: all non-document, non-null BSON
# types for the readConcern field are rejected.
KILLSESSIONS_READCONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"readconcern_type_{tid}",
        command=lambda ctx, v=val: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killSessions should reject {tid} readConcern",
    )
    for tid, val in [
        ("string", "local"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [1, 2]),
        ("binary", Binary(b"data")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [readConcern Subfield Rejection]: invalid subfields, unknown
# fields, and wrong types within the readConcern document are rejected.
KILLSESSIONS_READCONCERN_SUBFIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_unknown_subfield",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": {"bogusField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="killSessions should reject unknown subfield in readConcern",
    ),
    CommandTestCase(
        "readconcern_afterclustertime_valid_timestamp",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": {"afterClusterTime": Timestamp(1, 1)},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="killSessions should reject afterClusterTime in readConcern",
    ),
]

# Property [readConcern Level Type Rejection]: all non-string, non-null
# types for the readConcern level field are rejected.
KILLSESSIONS_READCONCERN_LEVEL_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"readconcern_level_type_{tid}",
        command=lambda ctx, v=val: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": {"level": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killSessions should reject {tid} type for readConcern level",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
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

KILLSESSIONS_READCONCERN_ERROR_TESTS: list[CommandTestCase] = (
    KILLSESSIONS_READCONCERN_LEVEL_ERROR_TESTS
    + KILLSESSIONS_READCONCERN_TYPE_ERROR_TESTS
    + KILLSESSIONS_READCONCERN_SUBFIELD_ERROR_TESTS
    + KILLSESSIONS_READCONCERN_LEVEL_TYPE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLSESSIONS_READCONCERN_ERROR_TESTS))
def test_killSessions_readconcern_error(collection, test):
    """Test killSessions readConcern field errors."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
