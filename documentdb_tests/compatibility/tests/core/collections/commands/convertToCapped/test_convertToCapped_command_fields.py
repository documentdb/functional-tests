"""Tests for convertToCapped command - ancillary command field handling."""

import datetime

import pytest
from bson import (
    Binary,
    Code,
    DBRef,
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
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [Comment Type Acceptance]: the comment field accepts any BSON
# type without affecting command success.
COMMENT_TYPE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "comment": v,
        },
        expected={"ok": 1.0},
        msg=f"comment={id} should be accepted",
    )
    for id, val in [
        ("string", "hello"),
        ("int32", 42),
        ("int64", Int64(99)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("null", None),
        ("array", [1, 2, 3]),
        ("object", {"key": "value"}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("binary", Binary(b"hello")),
        ("regex", Regex("pattern", "i")),
        ("code", Code("function() {}")),
        ("code_with_scope", Code("function() {}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("timestamp", Timestamp(1, 1)),
        ("datetime", datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)),
        ("dbref", DBRef("coll", "id")),
    ]
]

# Property [Unknown Command Fields]: unrecognized top-level command fields
# are silently accepted without error.
UNKNOWN_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "single_unknown_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "unknownField": "hello",
        },
        expected={"ok": 1.0},
        msg="Single unknown field should be silently accepted",
    ),
    CommandTestCase(
        "multiple_unknown_fields",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "foo": 42,
            "bar": [1, 2, 3],
            "baz": {"nested": True},
        },
        expected={"ok": 1.0},
        msg="Multiple unknown fields should be silently accepted",
    ),
]

# Property [bypassDocumentValidation Type Acceptance]: bypassDocumentValidation
# is accepted as a recognized command field with any BSON type without error.
BYPASS_DOC_VALIDATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"bypass_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "convertToCapped": ctx.collection,
            "size": 4096,
            "bypassDocumentValidation": v,
        },
        expected={"ok": 1.0},
        msg=f"bypassDocumentValidation={id} should be accepted",
    )
    for id, val in [
        ("string", "hello"),
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("3.14")),
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
        ("array", [1, 2, 3]),
        ("object", {"key": "value"}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"hello")),
        ("regex", Regex("pattern", "i")),
        ("code", Code("function() {}")),
        ("code_with_scope", Code("function() {}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

CONVERT_TO_CAPPED_COMMAND_FIELD_TESTS: list[CommandTestCase] = (
    COMMENT_TYPE_ACCEPTANCE_TESTS + UNKNOWN_FIELD_TESTS + BYPASS_DOC_VALIDATION_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CONVERT_TO_CAPPED_COMMAND_FIELD_TESTS))
def test_convert_to_capped_command_fields(database_client, collection, test):
    """Test convertToCapped command ancillary field handling."""
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
