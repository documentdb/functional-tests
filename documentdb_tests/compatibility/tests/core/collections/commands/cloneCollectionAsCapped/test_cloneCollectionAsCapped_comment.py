"""Tests for cloneCollectionAsCapped comment parameter acceptance."""

import functools
from datetime import datetime, timezone
from typing import Any

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
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Comment Parameter Acceptance]: the comment field accepts
# any BSON type without error.
COMMENT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": "hello",
        },
        expected={"ok": 1.0},
        msg="comment=string should succeed",
    ),
    CommandTestCase(
        "int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": 42,
        },
        expected={"ok": 1.0},
        msg="comment=int32 should succeed",
    ),
    CommandTestCase(
        "int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": Int64(42),
        },
        expected={"ok": 1.0},
        msg="comment=Int64 should succeed",
    ),
    CommandTestCase(
        "double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": 3.14,
        },
        expected={"ok": 1.0},
        msg="comment=double should succeed",
    ),
    CommandTestCase(
        "decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": Decimal128("99"),
        },
        expected={"ok": 1.0},
        msg="comment=Decimal128 should succeed",
    ),
    CommandTestCase(
        "bool_true",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": True,
        },
        expected={"ok": 1.0},
        msg="comment=True should succeed",
    ),
    CommandTestCase(
        "bool_false",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": False,
        },
        expected={"ok": 1.0},
        msg="comment=False should succeed",
    ),
    CommandTestCase(
        "null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": None,
        },
        expected={"ok": 1.0},
        msg="comment=null should succeed",
    ),
    CommandTestCase(
        "array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": [1, 2, 3],
        },
        expected={"ok": 1.0},
        msg="comment=array should succeed",
    ),
    CommandTestCase(
        "object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": {"key": "value"},
        },
        expected={"ok": 1.0},
        msg="comment=object should succeed",
    ),
    CommandTestCase(
        "objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": ObjectId("000000000000000000000001"),
        },
        expected={"ok": 1.0},
        msg="comment=ObjectId should succeed",
    ),
    CommandTestCase(
        "datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        expected={"ok": 1.0},
        msg="comment=datetime should succeed",
    ),
    CommandTestCase(
        "timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": Timestamp(1, 1),
        },
        expected={"ok": 1.0},
        msg="comment=Timestamp should succeed",
    ),
    CommandTestCase(
        "binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": Binary(b"hello"),
        },
        expected={"ok": 1.0},
        msg="comment=Binary should succeed",
    ),
    CommandTestCase(
        "regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": Regex("abc", "i"),
        },
        expected={"ok": 1.0},
        msg="comment=Regex should succeed",
    ),
    CommandTestCase(
        "code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": Code("function(){}"),
        },
        expected={"ok": 1.0},
        msg="comment=Code should succeed",
    ),
    CommandTestCase(
        "code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": Code("function(){}", {"x": 1}),
        },
        expected={"ok": 1.0},
        msg="comment=CodeWithScope should succeed",
    ),
    CommandTestCase(
        "minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": MinKey(),
        },
        expected={"ok": 1.0},
        msg="comment=MinKey should succeed",
    ),
    CommandTestCase(
        "maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": MaxKey(),
        },
        expected={"ok": 1.0},
        msg="comment=MaxKey should succeed",
    ),
    CommandTestCase(
        "deeply_nested_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": functools.reduce(
                lambda inner, _: {"n": inner},
                range(50),
                dict[str, Any](),
            ),
        },
        expected={"ok": 1.0},
        msg="comment=deeply nested object should succeed",
    ),
    CommandTestCase(
        "nested_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": [[1, [2, [3]]], [4, 5]],
        },
        expected={"ok": 1.0},
        msg="comment=nested array should succeed",
    ),
    CommandTestCase(
        "large_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": "x" * 10_000,
        },
        expected={"ok": 1.0},
        msg="comment=10KB string should succeed",
    ),
    CommandTestCase(
        "large_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": {f"k{i}": i for i in range(10_000)},
        },
        expected={"ok": 1.0},
        msg="comment=large object should succeed",
    ),
    CommandTestCase(
        "nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": FLOAT_NAN,
        },
        expected={"ok": 1.0},
        msg="comment=NaN should succeed",
    ),
    CommandTestCase(
        "infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": FLOAT_INFINITY,
        },
        expected={"ok": 1.0},
        msg="comment=Infinity should succeed",
    ),
    CommandTestCase(
        "negative_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": FLOAT_NEGATIVE_INFINITY,
        },
        expected={"ok": 1.0},
        msg="comment=-Infinity should succeed",
    ),
    CommandTestCase(
        "negative_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": DOUBLE_NEGATIVE_ZERO,
        },
        expected={"ok": 1.0},
        msg="comment=-0.0 should succeed",
    ),
    CommandTestCase(
        "null_bytes_in_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "comment": "hello\x00world",
        },
        expected={"ok": 1.0},
        msg="comment=string with null bytes should succeed",
    ),
    CommandTestCase(
        "omitted",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="omitting comment field should succeed",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMMENT_ACCEPTANCE_TESTS))
def test_clone_collection_as_capped_comment(database_client, collection, test):
    """Test cloneCollectionAsCapped comment parameter acceptance."""
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
