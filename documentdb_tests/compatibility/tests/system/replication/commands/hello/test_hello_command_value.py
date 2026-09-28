"""Tests for hello command value type acceptance.

Validates that the hello command accepts all standard BSON types as
the command value (the ``1`` in ``{hello: 1}``).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.compatibility.tests.system.replication.utils.replication_test_case import (  # noqa: E501
    ReplicationTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Command Value Type Acceptance]: the hello command accepts
# all standard BSON types as the command value.
HELLO_COMMAND_VALUE_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        f"command_value_{tid}",
        command=lambda ctx, v=val: {"hello": v},
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg=f"hello should accept {tid} as command value",
    )
    for tid, val in [
        ("int32", 1),
        ("bool_true", True),
        ("bool_false", False),
        ("double", 1.0),
        ("string", "test"),
        ("null", None),
        ("object_empty", {}),
        ("object", {"key": "val"}),
        ("array_empty", []),
        ("array", [1, 2]),
        ("int64", Int64(1)),
        ("decimal128", Decimal128("1")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("binary", Binary(b"\x00", 0)),
        ("objectid", ObjectId()),
        ("regex", Regex(".*")),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("code", Code("function(){}")),
    ]
]


@pytest.mark.parametrize("test", pytest_params(HELLO_COMMAND_VALUE_TESTS))
def test_hello_command_value(collection, test):
    """Test hello command value type acceptance."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
