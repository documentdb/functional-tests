"""Tests for planCacheClear command collection name field type validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import INVALID_NAMESPACE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field Type Rejection]: all non-string BSON types for the
# planCacheClear field produce INVALID_NAMESPACE_ERROR.
PLANCACHECLEAR_FIELD_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"field_type_{tid}",
        command=lambda ctx, v=val: {"planCacheClear": v},
        error_code=INVALID_NAMESPACE_ERROR,
        msg=f"planCacheClear should reject {tid} as collection name",
    )
    for tid, val in [
        ("int", 123),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
        ("array", []),
        ("object", {}),
        ("binary", Binary(b"\x00")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*")),
        ("timestamp", Timestamp(0, 0)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Namespace Edge Cases]: empty string and null byte collection
# names produce INVALID_NAMESPACE_ERROR.
PLANCACHECLEAR_NAMESPACE_EDGE_CASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "namespace_empty_string",
        command=lambda ctx: {"planCacheClear": ""},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheClear should reject empty string as collection name",
    ),
    CommandTestCase(
        "namespace_null_byte",
        command=lambda ctx: {"planCacheClear": "test\x00coll"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheClear should reject collection name containing null byte",
    ),
]

PLANCACHECLEAR_FIELD_TYPE_TESTS: list[CommandTestCase] = (
    PLANCACHECLEAR_FIELD_TYPE_ERROR_TESTS + PLANCACHECLEAR_NAMESPACE_EDGE_CASE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(PLANCACHECLEAR_FIELD_TYPE_TESTS))
def test_planCacheClear_field_type(database_client, collection, test):
    """Test planCacheClear field type and namespace validation."""
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
