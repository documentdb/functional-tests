"""Tests for count command legacy options and unknown option validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Legacy Recognized Options]: the fields option is silently accepted
# with no effect, and any BSON type is allowed for its value.
COUNT_LEGACY_RECOGNIZED_OPTIONS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"fields_{tid}",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx, v=val: {"count": ctx.collection, "fields": v},
        expected={"n": 3, "ok": 1.0},
        msg=f"count should silently accept fields={tid} with no effect",
    )
    for tid, val in [
        ("null", None),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("string", "hello"),
        ("bool", True),
        ("array", [1, 2, 3]),
        ("object", {"key": "value"}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02")),
        ("regex", Regex("^abc")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Unknown Option Validation]: unknown option names in the command
# document produce an error, and option name validation is case-sensitive.
COUNT_UNKNOWN_OPTION_VALIDATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_opt_case_sensitive_query",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "Query": {"x": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="count should reject 'Query' as unknown (case-sensitive)",
    ),
    CommandTestCase(
        "unknown_opt_case_sensitive_limit",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "Limit": 5},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="count should reject 'Limit' as unknown (case-sensitive)",
    ),
]

# Property [WriteConcern Rejection]: including writeConcern in the count command
# produces an error because count is a read operation that does not support it.
COUNT_WRITE_CONCERN_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "writeconcern_rejected",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "writeConcern": {"w": 1},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="count should reject writeConcern as unsupported",
    ),
]

COUNT_OPTIONS_TESTS: list[CommandTestCase] = (
    COUNT_LEGACY_RECOGNIZED_OPTIONS_TESTS
    + COUNT_UNKNOWN_OPTION_VALIDATION_TESTS
    + COUNT_WRITE_CONCERN_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COUNT_OPTIONS_TESTS))
def test_count_options(database_client, collection, test):
    """Test count command option handling."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
