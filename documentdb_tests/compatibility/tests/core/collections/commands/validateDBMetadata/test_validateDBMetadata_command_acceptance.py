"""Tests for validateDBMetadata command field value and null acceptance."""

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
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Command Field Value Acceptance]: the validateDBMetadata
# command field value is completely ignored and any BSON type is accepted.
VALIDATE_DB_METADATA_FIELD_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"value_{tid}",
        command={"validateDBMetadata": val, "apiParameters": {"version": "1", "strict": True}},
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg=f"validateDBMetadata should accept {tid} value",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(99)),
        ("double", 3.14),
        ("decimal128", Decimal128("42")),
        ("bool_true", True),
        ("string", "hello"),
        ("null", None),
        ("array", [1, 2, 3]),
        ("object", {"nested": "doc"}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"data")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Null and Missing Behavior (Success)]: optional fields set to
# null are treated as omitted and the command succeeds normally.
VALIDATE_DB_METADATA_NULL_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_db",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": None,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should succeed when db is null",
    ),
    CommandTestCase(
        "null_collection",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": None,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should succeed when collection is null",
    ),
    CommandTestCase(
        "null_max_time_ms",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "maxTimeMS": None,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should succeed when maxTimeMS is null",
    ),
    CommandTestCase(
        "null_read_concern",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "readConcern": None,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should succeed when readConcern is null",
    ),
    CommandTestCase(
        "null_write_concern",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "writeConcern": None,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should succeed when writeConcern is null",
    ),
]

VALIDATE_DB_METADATA_COMMAND_ACCEPTANCE_TESTS: list[CommandTestCase] = (
    VALIDATE_DB_METADATA_FIELD_VALUE_TESTS + VALIDATE_DB_METADATA_NULL_SUCCESS_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VALIDATE_DB_METADATA_COMMAND_ACCEPTANCE_TESTS))
def test_validateDBMetadata_command_acceptance(database_client, collection, test):
    """Test validateDBMetadata command field value and null acceptance."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
