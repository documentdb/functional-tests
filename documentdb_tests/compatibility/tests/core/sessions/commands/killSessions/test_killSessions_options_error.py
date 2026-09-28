"""Tests for killSessions writeConcern field errors."""

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
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.no_parallel

# Property [writeConcern Type Rejection]: all non-document, non-null BSON
# types for the writeConcern field are rejected.
KILLSESSIONS_WRITECONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"writeconcern_type_{tid}",
        command=lambda ctx, v=val: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "writeConcern": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killSessions should reject {tid} writeConcern",
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
        ("binary", Binary(b"data")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*")),
        ("timestamp", Timestamp(1, 1)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [writeConcern Document Rejection]: document values for
# writeConcern are rejected because the command does not support it.
KILLSESSIONS_WRITECONCERN_DOC_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"writeconcern_doc_{tid}",
        command=lambda ctx, v=val: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "writeConcern": v,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"killSessions should reject writeConcern {tid}",
    )
    for tid, val in [
        ("empty", {}),
        ("w_1", {"w": 1}),
        ("w_majority", {"w": "majority"}),
        ("j_true", {"j": True}),
    ]
]

KILLSESSIONS_OPTIONS_ERROR_TESTS: list[CommandTestCase] = (
    KILLSESSIONS_WRITECONCERN_TYPE_ERROR_TESTS + KILLSESSIONS_WRITECONCERN_DOC_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLSESSIONS_OPTIONS_ERROR_TESTS))
def test_killSessions_options_error(collection, test):
    """Test killSessions writeConcern field errors."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
