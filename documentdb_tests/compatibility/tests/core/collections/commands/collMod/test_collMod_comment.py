"""Tests for the collMod comment option."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, NotExists
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [comment Type Acceptance]: a comment of any BSON type representable
# by pymongo is accepted without changing the command result and is never echoed
# back in the response.
COLLMOD_COMMENT_TYPE_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_{tid}",
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "comment": v,
        },
        expected={"ok": Eq(1.0), "comment": NotExists()},
        msg=f"collMod should accept a {tid} comment without echoing it",
    )
    for tid, val in [
        ("string", "a note"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
        ("array", [1, "two", {"three": 3}]),
        ("object", {"reason": "audit"}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [comment Does Not Suppress Errors]: a comment paired with an
# otherwise-invalid option does not suppress the option's error.
COLLMOD_COMMENT_NO_SUPPRESS_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "no_suppress_index_type_error",
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "comment": "a note",
            "index": "not_an_object",
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="collMod should still reject an invalid index when a comment is present",
    ),
]

COLLMOD_COMMENT_ALL_TESTS: list[CommandTestCase] = (
    COLLMOD_COMMENT_TYPE_ACCEPTANCE_TESTS + COLLMOD_COMMENT_NO_SUPPRESS_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_COMMENT_ALL_TESTS))
def test_collMod_comment(database_client, collection, test):
    """Test collMod comment option behavior."""
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
