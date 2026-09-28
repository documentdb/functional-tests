"""Tests for collMod index argument presence, type, structure, and applicability."""

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
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, NotExists
from documentdb_tests.framework.target_collection import ViewCollection

# Property [Index Null No-Op]: an index value of null is accepted and treated
# as an omitted field, yielding a no-op success with no index modification
# echoed in the result.
COLLMOD_INDEX_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_no_op",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "index": None},
        expected={
            "ok": Eq(1.0),
            "expireAfterSeconds_new": NotExists(),
            "expireAfterSeconds_old": NotExists(),
            "hidden_new": NotExists(),
            "hidden_old": NotExists(),
            "prepareUnique_new": NotExists(),
            "prepareUnique_old": NotExists(),
            "unique_new": NotExists(),
            "unique_old": NotExists(),
        },
        msg="collMod should accept a null index as an omitted no-op",
    ),
]

# Property [Index Non-Document Type Rejection]: a non-document, non-null value
# for index produces a type-mismatch error.
COLLMOD_INDEX_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_{tid}",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "index": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} index value as a type mismatch",
    )
    for tid, val in [
        ("string", "a_1"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [{"name": "a_1"}]),
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

# Property [Empty Index Document Rejection]: an empty index document specifies
# neither an index name nor a key pattern and is rejected as an invalid option.
COLLMOD_INDEX_EMPTY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_document",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "index": {}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject an empty index document as an invalid option",
    ),
]

# Property [Unknown Index Sub-Field Rejection]: an unrecognized sub-field inside
# the index document is rejected as an unrecognized field.
COLLMOD_INDEX_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_subfield",
        indexes=[IndexModel([("a", 1)], name="a_1")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "index": {"name": "a_1", "bogus": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="collMod should reject an unknown index sub-field as an unrecognized field",
    ),
]

# Property [Index Unsupported Collection Type Rejection]: an index modification
# applied to a view is rejected as an invalid option, since the index option is
# not supported on a view.
COLLMOD_INDEX_VIEW_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_index_not_supported",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "collMod": ctx.collection,
            "index": {"name": "a_1", "hidden": True},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="collMod should reject an index modification on a view as an invalid option",
    ),
]

COLLMOD_INDEX_ARGUMENT_TESTS: list[CommandTestCase] = (
    COLLMOD_INDEX_NULL_TESTS
    + COLLMOD_INDEX_TYPE_ERROR_TESTS
    + COLLMOD_INDEX_EMPTY_ERROR_TESTS
    + COLLMOD_INDEX_UNKNOWN_FIELD_ERROR_TESTS
    + COLLMOD_INDEX_VIEW_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_INDEX_ARGUMENT_TESTS))
def test_collMod_index_argument(database_client, collection, test):
    """Test collMod index argument acceptance and structural rejection."""
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
