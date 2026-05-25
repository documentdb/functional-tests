"""Tests for convertToCapped writeConcern top-level validation."""

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
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [WriteConcern Top-Level Type Errors]: non-document BSON
# types for the writeConcern field produce TYPE_MISMATCH_ERROR.
WRITECONCERN_TOP_LEVEL_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{id} writeConcern should fail",
    )
    for id, val in [
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", [1, 2]),
        ("string", "hello"),
        ("objectid", ObjectId("000000000000000000000001")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01")),
        ("regex", Regex("abc", "i")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [WriteConcern Top-Level Acceptance]: omitted, null, and
# empty document writeConcern are accepted.
WRITECONCERN_TOP_LEVEL_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_omitted",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="Omitting writeConcern should succeed",
    ),
    CommandTestCase(
        "wc_empty_document",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {},
        },
        expected={"ok": 1.0},
        msg="Empty document writeConcern should be accepted",
    ),
    CommandTestCase(
        "wc_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": None,
        },
        expected={"ok": 1.0},
        msg="null writeConcern should be accepted",
    ),
]

WC_TOPLEVEL_TESTS: list[CommandTestCase] = (
    WRITECONCERN_TOP_LEVEL_TYPE_ERROR_TESTS + WRITECONCERN_TOP_LEVEL_ACCEPTANCE_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WC_TOPLEVEL_TESTS))
def test_convert_to_capped_wc_toplevel(database_client, collection, test):
    """Test convertToCapped writeConcern top-level validation."""
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
