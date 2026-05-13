"""Tests for count command namespace validation and count field type strictness."""

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
    INVALID_NAMESPACE_ERROR,
    INVALID_UUID_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Type Strictness: count]: only string type is accepted for the count
# field; all non-string types produce an invalid namespace error, except Binary
# subtype 4 (UUID, 16 bytes) which attempts UUID resolution, and Binary subtype 4
# with non-16-byte length which produces a malformed UUID error.
COUNT_TYPE_STRICTNESS_COUNT_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"type_count_{tid}",
            docs=None,
            command=lambda ctx, v=val: {"count": v},
            error_code=INVALID_NAMESPACE_ERROR,
            msg=f"count should reject {tid} for collection name",
        )
        for tid, val in [
            ("int32", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("null", None),
            ("array", [1, 2]),
            ("object", {"a": 1}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary_generic", Binary(b"\x01\x02\x03")),
            ("regex", Regex("^abc")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        "type_count_binary_uuid_16_bytes",
        docs=None,
        command=lambda ctx: {
            "count": Binary(
                b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10",
                4,
            )
        },
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="count with Binary UUID (16 bytes) should attempt UUID resolution and fail",
    ),
    CommandTestCase(
        "type_count_binary_uuid_short",
        docs=None,
        command=lambda ctx: {"count": Binary(b"\x01\x02\x03", 4)},
        error_code=INVALID_UUID_ERROR,
        msg="count with Binary UUID (non-16-byte) should produce malformed UUID error",
    ),
]

# Property [Namespace Validation Errors]: empty string, dot-prefixed names, and
# names containing null bytes produce an InvalidNamespace error.
COUNT_NAMESPACE_VALIDATION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "ns_err_empty_string",
        docs=None,
        command=lambda ctx: {"count": ""},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="count should reject empty string for collection name",
    ),
    CommandTestCase(
        "ns_err_dot_prefix",
        docs=None,
        command=lambda ctx: {"count": ".foo"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="count should reject collection name starting with a dot",
    ),
    CommandTestCase(
        "ns_err_null_byte",
        docs=None,
        command=lambda ctx: {"count": "foo\x00bar"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="count should reject collection name containing a null byte",
    ),
]

# Property [Namespace Validation Accepted]: all characters other than leading
# dot and embedded null are accepted, with no server-side length limit.
COUNT_NAMESPACE_VALIDATION_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "ns_ok_single_char",
        docs=None,
        command=lambda ctx: {"count": "a"},
        expected={"n": 0, "ok": 1.0},
        msg="count should accept a single-character collection name",
    ),
    CommandTestCase(
        "ns_ok_dollar_prefix",
        docs=None,
        command=lambda ctx: {"count": "$special"},
        expected={"n": 0, "ok": 1.0},
        msg="count should accept collection name starting with $",
    ),
    CommandTestCase(
        "ns_ok_mid_dot",
        docs=None,
        command=lambda ctx: {"count": "mid.dot"},
        expected={"n": 0, "ok": 1.0},
        msg="count should accept collection name with dot in the middle",
    ),
    CommandTestCase(
        "ns_ok_trailing_dot",
        docs=None,
        command=lambda ctx: {"count": "foo."},
        expected={"n": 0, "ok": 1.0},
        msg="count should accept collection name with trailing dot",
    ),
    CommandTestCase(
        "ns_ok_control_char",
        docs=None,
        command=lambda ctx: {"count": "foo\x01bar"},
        expected={"n": 0, "ok": 1.0},
        msg="count should accept collection name with control characters",
    ),
    CommandTestCase(
        "ns_ok_whitespace",
        docs=None,
        command=lambda ctx: {"count": "  spaces  "},
        expected={"n": 0, "ok": 1.0},
        msg="count should accept collection name with whitespace",
    ),
    CommandTestCase(
        "ns_ok_unicode_emoji",
        docs=None,
        command=lambda ctx: {"count": "\U0001f389emoji"},
        expected={"n": 0, "ok": 1.0},
        msg="count should accept collection name with unicode and emoji",
    ),
    CommandTestCase(
        "ns_ok_long_name",
        docs=None,
        command=lambda ctx: {"count": "x" * 10_000},
        expected={"n": 0, "ok": 1.0},
        msg="count should accept very long collection names without a length limit",
    ),
]

COUNT_NAMESPACE_VALIDATION_TESTS = (
    COUNT_NAMESPACE_VALIDATION_ERROR_TESTS + COUNT_NAMESPACE_VALIDATION_ACCEPTED_TESTS
)

COUNT_NAMESPACE_ALL_TESTS: list[CommandTestCase] = (
    COUNT_TYPE_STRICTNESS_COUNT_TESTS + COUNT_NAMESPACE_VALIDATION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COUNT_NAMESPACE_ALL_TESTS))
def test_count_namespace(database_client, collection, test):
    """Test count command namespace validation."""
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
