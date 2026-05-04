"""Tests for listCollections command."""

import functools
import uuid
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len
from documentdb_tests.framework.test_constants import (
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Comment BSON Type Acceptance]: the comment field accepts any
# BSON type without error, including special numeric values and large
# values.
COMMENT_BSON_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_string",
        command={"listCollections": 1, "comment": "hello"},
        msg="comment=string should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_int",
        command={"listCollections": 1, "comment": 42},
        msg="comment=int should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_int64",
        command={"listCollections": 1, "comment": Int64(42)},
        msg="comment=Int64 should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_float",
        command={"listCollections": 1, "comment": 3.14},
        msg="comment=float should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_decimal128",
        command={"listCollections": 1, "comment": Decimal128("99")},
        msg="comment=Decimal128 should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_bool_true",
        command={"listCollections": 1, "comment": True},
        msg="comment=True should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_bool_false",
        command={"listCollections": 1, "comment": False},
        msg="comment=False should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_array",
        command={"listCollections": 1, "comment": [1, 2, 3]},
        msg="comment=array should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_object",
        command={"listCollections": 1, "comment": {"key": "value"}},
        msg="comment=object should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_objectid",
        command=lambda _: {"listCollections": 1, "comment": ObjectId()},
        msg="comment=ObjectId should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_datetime",
        command={
            "listCollections": 1,
            "comment": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        msg="comment=datetime should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_timestamp",
        command={"listCollections": 1, "comment": Timestamp(1, 1)},
        msg="comment=Timestamp should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_binary",
        command={"listCollections": 1, "comment": Binary(b"hello")},
        msg="comment=Binary should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_binary_subtype_4",
        command=lambda _: {
            "listCollections": 1,
            "comment": Binary(uuid.uuid4().bytes, 4),
        },
        msg="comment=Binary subtype 4 (UUID) should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_binary_subtype_128",
        command={"listCollections": 1, "comment": Binary(b"hello", 128)},
        msg="comment=Binary user-defined subtype should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_regex",
        command={"listCollections": 1, "comment": Regex(".*")},
        msg="comment=Regex should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_code",
        command={"listCollections": 1, "comment": Code("function(){}")},
        msg="comment=Code should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_code_with_scope",
        command={
            "listCollections": 1,
            "comment": Code("function(){}", {"x": 1}),
        },
        msg="comment=CodeWithScope should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_minkey",
        command={"listCollections": 1, "comment": MinKey()},
        msg="comment=MinKey should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_maxkey",
        command={"listCollections": 1, "comment": MaxKey()},
        msg="comment=MaxKey should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_nan",
        command={"listCollections": 1, "comment": FLOAT_NAN},
        msg="comment=NaN should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_infinity",
        command={"listCollections": 1, "comment": FLOAT_INFINITY},
        msg="comment=Infinity should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_neg_infinity",
        command={"listCollections": 1, "comment": FLOAT_NEGATIVE_INFINITY},
        msg="comment=-Infinity should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_neg_zero",
        command={"listCollections": 1, "comment": DOUBLE_NEGATIVE_ZERO},
        msg="comment=-0.0 should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_large_string",
        command={"listCollections": 1, "comment": "x" * 10_000},
        msg="comment=large string should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_large_array",
        command={"listCollections": 1, "comment": list(range(10_000))},
        msg="comment=10K-element array should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="comment_deeply_nested_object",
        command=lambda _: {
            "listCollections": 1,
            "comment": functools.reduce(
                lambda inner, _: {"n": inner}, range(199), dict[str, Any]()
            ),
        },
        msg="comment=deeply nested object should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMMENT_BSON_TYPE_TESTS))
def test_listCollections_comment(database_client, collection, test):
    """Test listCollections command input acceptance and output structure."""
    target = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(target)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
