"""Tests for removeQuerySettings command error cases.

Validates that the removeQuerySettings command rejects invalid BSON types for
the primary argument, malformed query shapes, invalid hash strings, and
unrecognized top-level fields.
"""

from __future__ import annotations

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
    INVALID_LENGTH_ERROR,
    INVALID_NAMESPACE_ERROR,
    MISSING_FIELD_ERROR,
    QUERYSETTINGS_UNKNOWN_COMMAND_SHAPE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.requires(cluster_admin=True), pytest.mark.no_parallel]

# Property [Primary Argument Type Rejection]: the removeQuerySettings field
# must be a document or string. All other BSON types are rejected.
REMOVEQUERYSETTINGS_PRIMARY_ARG_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"primary_arg_{tid}",
        command=lambda ctx, v=value: {"removeQuerySettings": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"removeQuerySettings should reject {tid} as the primary argument",
    )
    for tid, value in [
        ("null", None),
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [1, 2, 3]),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(0, 0)),
        ("binary", Binary(b"\x00")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Query Shape Validation]: rejects malformed query shape documents
# including empty documents, missing/empty/null $db, and unknown command types.
REMOVEQUERYSETTINGS_QUERY_SHAPE_VALIDATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_shape_empty_document",
        command=lambda ctx: {"removeQuerySettings": {}},
        error_code=QUERYSETTINGS_UNKNOWN_COMMAND_SHAPE_ERROR,
        msg="removeQuerySettings should reject empty query shape document",
    ),
    CommandTestCase(
        "query_shape_missing_db",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
            }
        },
        error_code=MISSING_FIELD_ERROR,
        msg="removeQuerySettings should reject query shape missing $db field",
    ),
    CommandTestCase(
        "query_shape_empty_db",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
                "$db": "",
            }
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="removeQuerySettings should reject query shape with empty $db",
    ),
    CommandTestCase(
        "query_shape_null_db",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
                "$db": None,
            }
        },
        error_code=MISSING_FIELD_ERROR,
        msg="removeQuerySettings should reject query shape with null $db",
    ),
    CommandTestCase(
        "query_shape_unknown_command",
        command=lambda ctx: {
            "removeQuerySettings": {
                "unknownCommand": ctx.collection,
                "filter": {"x": 1},
                "$db": ctx.database,
            }
        },
        error_code=QUERYSETTINGS_UNKNOWN_COMMAND_SHAPE_ERROR,
        msg="removeQuerySettings should reject unknown command type in query shape",
    ),
    CommandTestCase(
        "query_shape_no_command_type",
        command=lambda ctx: {
            "removeQuerySettings": {
                "filter": {"x": 1},
                "$db": ctx.database,
            }
        },
        error_code=QUERYSETTINGS_UNKNOWN_COMMAND_SHAPE_ERROR,
        msg="removeQuerySettings should reject query shape without a command type",
    ),
]

# Property [Hash String Validation]: rejects invalid hash string formats
# including empty, too short, too long, and non-hexadecimal strings.
REMOVEQUERYSETTINGS_HASH_VALIDATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_hash_string",
        command=lambda ctx: {"removeQuerySettings": ""},
        error_code=INVALID_LENGTH_ERROR,
        msg="removeQuerySettings should reject empty hash string",
    ),
    CommandTestCase(
        "short_hash_string",
        command=lambda ctx: {"removeQuerySettings": "ABCD"},
        error_code=INVALID_LENGTH_ERROR,
        msg="removeQuerySettings should reject short hash string",
    ),
    CommandTestCase(
        "long_hash_string",
        command=lambda ctx: {"removeQuerySettings": "AA" * 33},
        error_code=INVALID_LENGTH_ERROR,
        msg="removeQuerySettings should reject hash string longer than 64 chars",
    ),
    CommandTestCase(
        "non_hex_hash_string",
        command=lambda ctx: {
            "removeQuerySettings": "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG"
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG"
        },
        error_code=BAD_VALUE_ERROR,
        msg="removeQuerySettings should reject non-hex hash string",
    ),
]

# Property [Unrecognized Fields]: rejects unknown top-level command fields
# and fields valid for setQuerySettings but not removeQuerySettings.
REMOVEQUERYSETTINGS_UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unrecognized_top_level_field",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
                "$db": ctx.database,
            },
            "unknownField": 1,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="removeQuerySettings should reject unrecognized top-level field",
    ),
    CommandTestCase(
        "settings_field_rejected",
        command=lambda ctx: {
            "removeQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
                "$db": ctx.database,
            },
            "settings": {"reject": True},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="removeQuerySettings should reject settings field",
    ),
]

REMOVEQUERYSETTINGS_ERROR_TESTS: list[CommandTestCase] = (
    REMOVEQUERYSETTINGS_PRIMARY_ARG_TYPE_TESTS
    + REMOVEQUERYSETTINGS_QUERY_SHAPE_VALIDATION_TESTS
    + REMOVEQUERYSETTINGS_HASH_VALIDATION_TESTS
    + REMOVEQUERYSETTINGS_UNRECOGNIZED_FIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(REMOVEQUERYSETTINGS_ERROR_TESTS))
def test_removeQuerySettings_error(collection, test):
    """Test removeQuerySettings error cases."""
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        error_code=test.error_code,
        msg=test.msg,
    )
