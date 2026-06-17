"""Tests for the collMod writeConcern option."""

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
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [writeConcern Success]: a top-level writeConcern of null is treated
# as omitted and an empty document is accepted, both succeeding without changing
# the command result.
COLLMOD_WRITE_CONCERN_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_treated_as_omitted",
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "writeConcern": None,
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should treat a null writeConcern as omitted",
    ),
    CommandTestCase(
        "empty_document",
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "writeConcern": {},
        },
        expected={"ok": Eq(1.0)},
        msg="collMod should accept an empty writeConcern document",
    ),
]

# Property [writeConcern.w Portable Acceptance]: a number that resolves to 0 or
# 1 (after truncation), the "majority" tag, and an object tag are accepted on
# every topology without changing the command result.
COLLMOD_WRITE_CONCERN_W_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"w_{wid}",
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "writeConcern": {"w": v},
        },
        expected={"ok": Eq(1.0)},
        msg=f"collMod should accept a {wid} writeConcern.w value on any topology",
    )
    for wid, val in [
        ("int_zero", 0),
        ("int_one", 1),
        ("double_fractional", 1.5),
        ("int64_one", Int64(1)),
        ("decimal_one", Decimal128("1")),
        ("string_majority", "majority"),
        ("object", {"a": 1}),
    ]
]

# Property [writeConcern.w Quorum Acceptance On Replica Set]: a quorum write
# concern (a number above 1, an unrecognized string tag, the empty string, or
# null) is accepted on a replica set, where an unsatisfiable concern surfaces
# asynchronously as a writeConcernError so the command still returns ok:1.0.
COLLMOD_WRITE_CONCERN_W_QUORUM_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"w_quorum_{wid}",
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "writeConcern": {"w": v},
        },
        expected={"ok": Eq(1.0)},
        msg=f"collMod should accept a {wid} quorum writeConcern.w on a replica set",
        marks=(pytest.mark.requires(quorum_write_concern=True),),
    )
    for wid, val in [
        ("int_fifty", 50),
        ("decimal_above_one", Decimal128("5")),
        ("string_arbitrary", "foo"),
        ("string_empty", ""),
        ("null", None),
    ]
]

# Property [writeConcern.j Acceptance]: a numeric, bool, or null value is
# accepted for writeConcern.j without changing the command result.
COLLMOD_WRITE_CONCERN_J_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"j_{jid}",
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "writeConcern": {"j": v},
        },
        expected={"ok": Eq(1.0)},
        msg=f"collMod should accept a {jid} writeConcern.j value",
    )
    for jid, val in [
        ("bool_true", True),
        ("bool_false", False),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal", Decimal128("1")),
        ("null", None),
    ]
]

# Property [writeConcern.wtimeout Acceptance]: writeConcern.wtimeout is not
# validated in this context, so a negative number and an arbitrary string are
# both accepted without changing the command result.
COLLMOD_WRITE_CONCERN_WTIMEOUT_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wtimeout_{wid}",
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "writeConcern": {"wtimeout": v},
        },
        expected={"ok": Eq(1.0)},
        msg=f"collMod should accept a {wid} writeConcern.wtimeout value",
    )
    for wid, val in [
        ("negative_number", -5),
        ("arbitrary_string", "foo"),
    ]
]

# Property [writeConcern.j Type Rejection]: any writeConcern.j value whose type
# is outside the accepted numeric and bool types produces a TypeMismatch error.
COLLMOD_WRITE_CONCERN_J_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"j_type_{tid}",
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "writeConcern": {"j": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} writeConcern.j as a non-numeric/bool",
    )
    for tid, val in [
        ("string", "x"),
        ("array", [1, 2]),
        ("object", {"a": 1}),
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

# Property [writeConcern Type Rejection]: a non-object, non-null top-level
# writeConcern produces a TypeMismatch error.
COLLMOD_WRITE_CONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_{tid}",
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "writeConcern": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} writeConcern as a non-object",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [1, 2]),
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

# Property [writeConcern.w Range Rejection]: a numeric writeConcern.w outside
# the inclusive supported range (after truncation) produces a parse error.
COLLMOD_WRITE_CONCERN_W_RANGE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"w_range_{wid}",
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "writeConcern": {"w": v},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"collMod should reject an out-of-range writeConcern.w of {wid}",
    )
    for wid, val in [
        ("fifty_one", 51),
        ("negative_one", -1),
        ("decimal_above_fifty", Decimal128("123.45")),
    ]
]

# Property [writeConcern.w Type Rejection]: a writeConcern.w value that is not a
# number, string, or object produces a parse error.
COLLMOD_WRITE_CONCERN_W_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"w_type_{tid}",
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "writeConcern": {"w": v},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"collMod should reject a {tid} writeConcern.w as non-number/string/object",
    )
    for tid, val in [
        ("bool_true", True),
        ("bool_false", False),
        ("array", [1, 2]),
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

# Property [writeConcern.w Quorum Rejection On Standalone]: a quorum write
# concern (a number above 1, an unrecognized string tag, the empty string, or
# null) is rejected up front on a standalone with a BadValue error, since a
# standalone can never satisfy a quorum concern.
COLLMOD_WRITE_CONCERN_W_QUORUM_STANDALONE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"w_quorum_reject_{wid}",
        docs=[],
        command=lambda ctx, v=val: {
            "collMod": ctx.collection,
            "writeConcern": {"w": v},
        },
        error_code=BAD_VALUE_ERROR,
        msg=f"collMod should reject a {wid} quorum writeConcern.w up front on a standalone",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    )
    for wid, val in [
        ("int_fifty", 50),
        ("decimal_above_one", Decimal128("5")),
        ("string_arbitrary", "foo"),
        ("string_empty", ""),
        ("null", None),
    ]
]

# Property [writeConcern Unknown Field Rejection]: an unrecognized writeConcern
# sub-field, and a write concern option placed at the top level instead of
# nested under writeConcern, each produce an unknown-field error.
COLLMOD_WRITE_CONCERN_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_subfield",
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "writeConcern": {"bogus": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="collMod should reject an unknown writeConcern sub-field",
    ),
    CommandTestCase(
        "bare_top_level_w",
        docs=[],
        command=lambda ctx: {
            "collMod": ctx.collection,
            "w": 1,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="collMod should reject a bare top-level w not nested under writeConcern",
    ),
]

COLLMOD_WRITE_CONCERN_ALL_TESTS: list[CommandTestCase] = (
    COLLMOD_WRITE_CONCERN_SUCCESS_TESTS
    + COLLMOD_WRITE_CONCERN_W_SUCCESS_TESTS
    + COLLMOD_WRITE_CONCERN_W_QUORUM_SUCCESS_TESTS
    + COLLMOD_WRITE_CONCERN_J_SUCCESS_TESTS
    + COLLMOD_WRITE_CONCERN_WTIMEOUT_SUCCESS_TESTS
    + COLLMOD_WRITE_CONCERN_J_TYPE_ERROR_TESTS
    + COLLMOD_WRITE_CONCERN_TYPE_ERROR_TESTS
    + COLLMOD_WRITE_CONCERN_W_RANGE_ERROR_TESTS
    + COLLMOD_WRITE_CONCERN_W_TYPE_ERROR_TESTS
    + COLLMOD_WRITE_CONCERN_W_QUORUM_STANDALONE_ERROR_TESTS
    + COLLMOD_WRITE_CONCERN_UNKNOWN_FIELD_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_WRITE_CONCERN_ALL_TESTS))
def test_collMod_write_concern(database_client, collection, test):
    """Test collMod writeConcern option behavior."""
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
