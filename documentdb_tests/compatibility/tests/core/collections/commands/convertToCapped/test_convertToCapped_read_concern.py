"""Tests for convertToCapped readConcern behavior."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [readConcern Success Behavior]: readConcern with level
# "local", as an empty document, or as null is accepted.
READ_CONCERN_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="read_concern_local",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "readConcern": {"level": "local"},
        },
        expected={"ok": Eq(1.0)},
        msg="readConcern with level 'local' should succeed",
    ),
    CommandTestCase(
        id="read_concern_empty",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "readConcern": {},
        },
        expected={"ok": Eq(1.0)},
        msg="readConcern={} should succeed",
    ),
    CommandTestCase(
        id="read_concern_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "readConcern": None,
        },
        expected={"ok": Eq(1.0)},
        msg="readConcern=null should succeed",
    ),
]

# Property [readConcern Level Unsupported]: non-local read concern
# levels produce INVALID_OPTIONS_ERROR.
READ_CONCERN_LEVEL_UNSUPPORTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"unsupported_level_{level}",
        docs=[{"_id": 1}],
        command=lambda ctx, lvl=level: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "readConcern": {"level": lvl},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"readConcern level '{level}' should produce INVALID_OPTIONS_ERROR",
    )
    for level in ["available", "majority", "linearizable", "snapshot"]
]

# Property [readConcern Level Invalid Name]: an unrecognized read
# concern level name produces BAD_VALUE_ERROR.
READ_CONCERN_LEVEL_INVALID_NAME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="invalid_level",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "readConcern": {"level": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="readConcern level 'invalid' should produce BAD_VALUE_ERROR",
    ),
]

# Property [readConcern Type Errors]: when readConcern is a
# non-document BSON type (excluding null), the command produces a TYPE_MISMATCH_ERROR.
READ_CONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"read_concern_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "readConcern": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"readConcern={id} should produce TYPE_MISMATCH_ERROR",
    )
    for id, val in [
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("99")),
        ("bool", True),
        ("string", "local"),
        ("array", [{"level": "local"}]),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"hello")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

READ_CONCERN_TESTS: list[CommandTestCase] = (
    READ_CONCERN_SUCCESS_TESTS
    + READ_CONCERN_LEVEL_UNSUPPORTED_TESTS
    + READ_CONCERN_LEVEL_INVALID_NAME_TESTS
    + READ_CONCERN_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(READ_CONCERN_TESTS))
def test_convert_to_capped_read_concern(database_client, collection, test):
    """Test convertToCapped readConcern behavior."""
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
