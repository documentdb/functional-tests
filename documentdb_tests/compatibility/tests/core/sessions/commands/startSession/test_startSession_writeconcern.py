"""Tests for startSession writeConcern handling."""

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
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [writeConcern Type Rejection]: non-document writeConcern values produce a type error.
STARTSESSION_WC_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_type_reject_{tid}",
        command=lambda ctx, v=val: {"startSession": 1, "writeConcern": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"startSession should reject {tid} writeConcern with type mismatch error",
    )
    for tid, val in [
        ("string", "majority"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("empty_array", []),
        ("non_empty_array", [1, 2]),
        ("binary", Binary(b"\x00\x01\x02")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*", "i")),
        ("timestamp", Timestamp(1, 1)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [writeConcern Document Rejection]: document writeConcern values
# are rejected as invalid options.
STARTSESSION_WC_DOC_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_doc_reject_empty",
        command=lambda ctx: {"startSession": 1, "writeConcern": {}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="startSession should reject empty document writeConcern",
    ),
    CommandTestCase(
        "wc_doc_reject_w1",
        command=lambda ctx: {"startSession": 1, "writeConcern": {"w": 1}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="startSession should reject writeConcern with w:1",
    ),
    CommandTestCase(
        "wc_doc_reject_w_majority",
        command=lambda ctx: {"startSession": 1, "writeConcern": {"w": "majority"}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="startSession should reject writeConcern with w:majority",
    ),
    CommandTestCase(
        "wc_doc_reject_j_true",
        command=lambda ctx: {"startSession": 1, "writeConcern": {"j": True}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="startSession should reject writeConcern with j:true",
    ),
]

# Property [writeConcern Null Acceptance]: null writeConcern is treated as omitted.
STARTSESSION_WC_NULL_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_null_accepted",
        command=lambda ctx: {"startSession": 1, "writeConcern": None},
        expected={"ok": Eq(1.0)},
        msg="startSession should accept null writeConcern as omitted",
    ),
]

STARTSESSION_WC_SUCCESS_TESTS = STARTSESSION_WC_NULL_ACCEPTANCE_TESTS

STARTSESSION_WC_ERROR_TESTS = (
    STARTSESSION_WC_TYPE_REJECTION_TESTS + STARTSESSION_WC_DOC_REJECTION_TESTS
)

STARTSESSION_WC_TESTS = STARTSESSION_WC_SUCCESS_TESTS + STARTSESSION_WC_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_WC_TESTS))
def test_startSession_writeconcern(database_client, collection, test):
    """Test startSession writeConcern handling."""
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
