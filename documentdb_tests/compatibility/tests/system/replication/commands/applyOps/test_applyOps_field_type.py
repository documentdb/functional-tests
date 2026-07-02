"""Tests for applyOps command field type rejection."""

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
)
from documentdb_tests.compatibility.tests.system.replication.utils.replication_test_case import (  # noqa: E501
    ReplicationTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.requires(replication=True), pytest.mark.no_parallel]


# Property [Command Field Type Rejection]: the applyOps command field expects
# an array. All non-array BSON types are rejected.
APPLYOPS_FIELD_TYPE_ERROR_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        f"field_type_{tid}",
        command=lambda ctx, v=val: {"applyOps": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"applyOps should reject {tid} as command field value",
    )
    for tid, val in [
        ("int32_positive", 1),
        ("int32_zero", 0),
        ("int32_negative", -1),
        ("int64", Int64(1)),
        ("int64_max", Int64(9_223_372_036_854_775_807)),
        ("double", 1.0),
        ("double_zero", 0.0),
        ("double_negative", -1.0),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("nan", float("nan")),
        ("infinity", float("inf")),
        ("string", "test"),
        ("string_empty", ""),
        ("object_empty", {}),
        ("object", {"key": "value"}),
        ("binary", Binary(b"\x00\x01\x02")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*", "i")),
        ("timestamp", Timestamp(1, 1)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
] + [
    # Null also produces a type mismatch error.
    ReplicationTestCase(
        "field_type_null",
        command=lambda ctx: {"applyOps": None},
        error_code=TYPE_MISMATCH_ERROR,
        msg="applyOps should reject null as command field value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(APPLYOPS_FIELD_TYPE_ERROR_TESTS))
def test_applyOps_field_type(collection, test):
    """Test applyOps command field type rejection."""
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertFailureCode(result, test.error_code, msg=test.msg)
