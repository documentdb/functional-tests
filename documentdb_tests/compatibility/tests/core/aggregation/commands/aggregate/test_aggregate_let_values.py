"""Tests for aggregate command let variable value acceptance."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
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
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [Let Variable Values]: let variables accept all BSON types as values
# including expressions and $$REMOVE.
AGGREGATE_LET_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "let_value_string_null_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"s": "$$vStr", "n": "$$vNull", "b": "$$vBool"}}],
            "cursor": {},
            "let": {"vStr": "hello", "vNull": None, "vBool": True},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "s": "hello", "n": None, "b": True}])},
        },
        msg="aggregate should accept string, null, and boolean variable values",
    ),
    CommandTestCase(
        "let_value_numeric_types",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$addFields": {
                        "i": "$$vInt",
                        "l": "$$vLong",
                        "d": "$$vDbl",
                        "dec": "$$vDec",
                    }
                }
            ],
            "cursor": {},
            "let": {
                "vInt": 42,
                "vLong": Int64(123456789012345),
                "vDbl": 3.14,
                "vDec": DECIMAL128_ONE_AND_HALF,
            },
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq(
                    [
                        {
                            "_id": 1,
                            "i": 42,
                            "l": Int64(123456789012345),
                            "d": 3.14,
                            "dec": DECIMAL128_ONE_AND_HALF,
                        }
                    ]
                )
            },
        },
        msg="aggregate should accept int32, Int64, double, and Decimal128 variable values",
    ),
    CommandTestCase(
        "let_value_complex_types",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"a": "$$vArr", "o": "$$vDoc"}}],
            "cursor": {},
            "let": {"vArr": [1, 2, 3], "vDoc": {"nested": "doc"}},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "a": [1, 2, 3], "o": {"nested": "doc"}}])},
        },
        msg="aggregate should accept array and document variable values",
    ),
    CommandTestCase(
        "let_value_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$v"}}],
            "cursor": {},
            "let": {"v": ObjectId("507f1f77bcf86cd799439011")},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": ObjectId("507f1f77bcf86cd799439011")}])},
        },
        msg="aggregate should accept ObjectId variable value",
    ),
    CommandTestCase(
        "let_value_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$v"}}],
            "cursor": {},
            "let": {"v": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq(
                    [{"_id": 1, "y": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)}]
                )
            },
        },
        msg="aggregate should accept datetime variable value",
    ),
    CommandTestCase(
        "let_value_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$v"}}],
            "cursor": {},
            "let": {"v": Binary(b"hello")},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": b"hello"}])},
        },
        msg="aggregate should accept Binary variable value",
    ),
    CommandTestCase(
        "let_value_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$v"}}],
            "cursor": {},
            "let": {"v": Regex("abc", "i")},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": Regex("abc", "i")}])},
        },
        msg="aggregate should accept Regex variable value",
    ),
    CommandTestCase(
        "let_value_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$v"}}],
            "cursor": {},
            "let": {"v": Code("function(){}")},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": Code("function(){}")}])},
        },
        msg="aggregate should accept Code variable value",
    ),
    CommandTestCase(
        "let_value_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$v"}}],
            "cursor": {},
            "let": {"v": Code("function(){}", {"x": 1})},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": Code("function(){}", {"x": 1})}])},
        },
        msg="aggregate should accept Code with scope variable value",
    ),
    CommandTestCase(
        "let_value_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$v"}}],
            "cursor": {},
            "let": {"v": MinKey()},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": MinKey()}])},
        },
        msg="aggregate should accept MinKey variable value",
    ),
    CommandTestCase(
        "let_value_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$v"}}],
            "cursor": {},
            "let": {"v": MaxKey()},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": MaxKey()}])},
        },
        msg="aggregate should accept MaxKey variable value",
    ),
    CommandTestCase(
        "let_value_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$v"}}],
            "cursor": {},
            "let": {"v": Timestamp(1_234_567_890, 1)},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": Timestamp(1_234_567_890, 1)}])},
        },
        msg="aggregate should accept Timestamp variable value",
    ),
    CommandTestCase(
        "let_value_expression_add",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$computed"}}],
            "cursor": {},
            "let": {"computed": {"$add": [1, 2]}},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "y": 3}])},
        },
        msg="aggregate should evaluate $add expression in let variable value",
    ),
    CommandTestCase(
        "let_value_remove",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"y": "$$myVar"}}],
            "cursor": {},
            "let": {"myVar": "$$REMOVE"},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"firstBatch": Eq([{"_id": 1, "x": 10}])},
        },
        msg="aggregate should support $$REMOVE as variable value causing field exclusion",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_LET_VALUE_TESTS))
def test_aggregate_let_values(database_client, collection, test):
    """Test aggregate let variable value acceptance."""
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
