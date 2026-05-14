"""Tests for compact command comment field acceptance."""

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
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Comment Acceptance]: the comment field accepts any BSON value
# without error.
COMPACT_COMMENT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "comment_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": "hello"},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=string should be accepted",
    ),
    CommandTestCase(
        "comment_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": 42},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=int32 should be accepted",
    ),
    CommandTestCase(
        "comment_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": Int64(42)},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=Int64 should be accepted",
    ),
    CommandTestCase(
        "comment_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": 3.14},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=double should be accepted",
    ),
    CommandTestCase(
        "comment_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": Decimal128("99")},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=Decimal128 should be accepted",
    ),
    CommandTestCase(
        "comment_bool_true",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": True},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=True should be accepted",
    ),
    CommandTestCase(
        "comment_bool_false",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": False},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=False should be accepted",
    ),
    CommandTestCase(
        "comment_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": [1, 2, 3]},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=array should be accepted",
    ),
    CommandTestCase(
        "comment_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": {"key": "value"}},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=object should be accepted",
    ),
    CommandTestCase(
        "comment_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": ObjectId()},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=ObjectId should be accepted",
    ),
    CommandTestCase(
        "comment_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "comment": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=datetime should be accepted",
    ),
    CommandTestCase(
        "comment_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": Timestamp(1, 1)},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=Timestamp should be accepted",
    ),
    CommandTestCase(
        "comment_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": Binary(b"hello")},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=Binary should be accepted",
    ),
    CommandTestCase(
        "comment_binary_subtype_4",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "comment": Binary(uuid.uuid4().bytes, 4),
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=Binary subtype 4 (UUID) should be accepted",
    ),
    CommandTestCase(
        "comment_binary_subtype_128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "comment": Binary(b"hello", 128),
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=Binary user-defined subtype should be accepted",
    ),
    CommandTestCase(
        "comment_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": Regex(".*")},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=Regex should be accepted",
    ),
    CommandTestCase(
        "comment_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": Code("function(){}")},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=Code should be accepted",
    ),
    CommandTestCase(
        "comment_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "comment": Code("function(){}", {"x": 1}),
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=CodeWithScope should be accepted",
    ),
    CommandTestCase(
        "comment_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": MinKey()},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=MinKey should be accepted",
    ),
    CommandTestCase(
        "comment_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": MaxKey()},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=MaxKey should be accepted",
    ),
    CommandTestCase(
        "comment_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": FLOAT_NAN},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=NaN should be accepted",
    ),
    CommandTestCase(
        "comment_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": FLOAT_INFINITY},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=Infinity should be accepted",
    ),
    CommandTestCase(
        "comment_neg_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "comment": FLOAT_NEGATIVE_INFINITY,
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=-Infinity should be accepted",
    ),
    CommandTestCase(
        "comment_neg_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": DOUBLE_NEGATIVE_ZERO},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=-0.0 should be accepted",
    ),
    CommandTestCase(
        "comment_decimal128_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": DECIMAL128_NAN},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=Decimal128 NaN should be accepted",
    ),
    CommandTestCase(
        "comment_decimal128_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": DECIMAL128_INFINITY},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=Decimal128 Infinity should be accepted",
    ),
    CommandTestCase(
        "comment_decimal128_neg_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "comment": DECIMAL128_NEGATIVE_INFINITY,
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=Decimal128 -Infinity should be accepted",
    ),
    CommandTestCase(
        "comment_decimal128_neg_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "comment": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=Decimal128 -0 should be accepted",
    ),
    CommandTestCase(
        "comment_empty_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": ""},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=empty string should be accepted",
    ),
    CommandTestCase(
        "comment_empty_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": []},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=empty array should be accepted",
    ),
    CommandTestCase(
        "comment_empty_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": {}},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=empty object should be accepted",
    ),
    CommandTestCase(
        "comment_large_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": "x" * 10_000},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=large string should be accepted",
    ),
    CommandTestCase(
        "comment_large_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": list(range(10_000))},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=10K-element array should be accepted",
    ),
    CommandTestCase(
        "comment_deeply_nested_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "comment": functools.reduce(lambda inner, _: {"n": inner}, range(99), dict[str, Any]()),
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=deeply nested object should be accepted",
    ),
    CommandTestCase(
        "comment_nested_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "comment": [[1, [2, [3]]]],
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=nested array should be accepted",
    ),
    CommandTestCase(
        "comment_mixed_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "comment": [1, "two", True, None, {"k": "v"}, [3]],
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=mixed-type array should be accepted",
    ),
    CommandTestCase(
        "comment_null_byte_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": "a\x00b"},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=string with null byte should be accepted",
    ),
    CommandTestCase(
        "comment_emoji_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": "\U0001f600"},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=emoji string should be accepted",
    ),
    CommandTestCase(
        "comment_dollar_prefix",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": "$test"},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="comment=$ prefix string should be accepted",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMPACT_COMMENT_ACCEPTANCE_TESTS))
def test_compact_comment(database_client, collection, test):
    """Test compact command comment field accepts any BSON value."""
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
