"""Tests for aggregate command cursor field acceptance."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Ne
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_MAX,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_NAN,
    INT64_MAX,
    INT64_ZERO,
)

# Property [Cursor Default Batch Size]: an empty cursor document or null
# batchSize uses the default batch size of 101.
AGGREGATE_CURSOR_DEFAULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursor_empty_default_batch",
        docs=[{"_id": i} for i in range(150)],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}},
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": i} for i in range(101)]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should use default batch size of 101 with empty cursor document",
    ),
    CommandTestCase(
        "cursor_batchsize_null",
        docs=[{"_id": i} for i in range(150)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": None},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": i} for i in range(101)]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should treat null batchSize as the default of 101",
    ),
]

# Property [Cursor batchSize Type Acceptance]: batchSize accepts int32, Int64,
# double, and Decimal128 numeric types.
AGGREGATE_CURSOR_BATCHSIZE_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursor_batchsize_int32",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": 2},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 0}, {"_id": 1}]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should limit firstBatch to the requested batchSize",
    ),
    CommandTestCase(
        "cursor_batchsize_int64",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": Int64(3)},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 0}, {"_id": 1}, {"_id": 2}]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should accept Int64 batchSize",
    ),
    CommandTestCase(
        "cursor_batchsize_double",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": 2.0},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 0}, {"_id": 1}]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should accept double batchSize",
    ),
    CommandTestCase(
        "cursor_batchsize_decimal128",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": Decimal128("3")},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 0}, {"_id": 1}, {"_id": 2}]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should accept Decimal128 batchSize",
    ),
]

# Property [Cursor batchSize Zero]: batchSize 0 and negative-zero produce an
# empty firstBatch with an open cursor.
AGGREGATE_CURSOR_BATCHSIZE_ZERO_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursor_batchsize_zero",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": 0},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should return empty firstBatch with open cursor for batchSize 0",
    ),
    CommandTestCase(
        "cursor_batchsize_neg_zero_double",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": DOUBLE_NEGATIVE_ZERO},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should treat -0.0 batchSize as 0",
    ),
    CommandTestCase(
        "cursor_batchsize_neg_zero_decimal128",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": DECIMAL128_NEGATIVE_ZERO},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should treat Decimal128('-0') batchSize as 0",
    ),
]

# Property [Cursor batchSize Double Truncation]: fractional double values are
# truncated toward zero.
AGGREGATE_CURSOR_BATCHSIZE_DOUBLE_TRUNCATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursor_batchsize_double_truncate_1_5",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": 1.5},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 0}]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should truncate double batchSize 1.5 toward zero to 1",
    ),
    CommandTestCase(
        "cursor_batchsize_double_truncate_2_5",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": 2.5},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 0}, {"_id": 1}]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should truncate double batchSize 2.5 toward zero to 2",
    ),
    CommandTestCase(
        "cursor_batchsize_double_truncate_neg_0_9",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": -0.9},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should truncate double batchSize -0.9 toward zero to 0",
    ),
]

# Property [Cursor batchSize Decimal128 Rounding]: fractional Decimal128 values
# are rounded via banker's rounding (round half to even).
AGGREGATE_CURSOR_BATCHSIZE_DECIMAL128_ROUNDING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursor_batchsize_decimal128_bankers_0_5",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": DECIMAL128_HALF},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should round Decimal128 batchSize 0.5 to 0 via banker's rounding",
    ),
    CommandTestCase(
        "cursor_batchsize_decimal128_bankers_1_5",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": DECIMAL128_ONE_AND_HALF},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 0}, {"_id": 1}]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should round Decimal128 batchSize 1.5 to 2 via banker's rounding",
    ),
    CommandTestCase(
        "cursor_batchsize_decimal128_bankers_2_5",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": DECIMAL128_TWO_AND_HALF},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 0}, {"_id": 1}]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should round Decimal128 batchSize 2.5 to 2 via banker's rounding",
    ),
    CommandTestCase(
        "cursor_batchsize_decimal128_bankers_3_5",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": Decimal128("3.5")},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": 0}, {"_id": 1}, {"_id": 2}, {"_id": 3}]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should round Decimal128 batchSize 3.5 to 4 via banker's rounding",
    ),
    CommandTestCase(
        "cursor_batchsize_decimal128_neg_half",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": DECIMAL128_NEGATIVE_HALF},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should round Decimal128 batchSize -0.5 to 0 via banker's rounding",
    ),
]

# Property [Cursor batchSize NaN]: NaN values in any numeric type are treated
# as batchSize 0.
AGGREGATE_CURSOR_BATCHSIZE_NAN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursor_batchsize_nan",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": FLOAT_NAN},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should treat NaN batchSize as 0",
    ),
    CommandTestCase(
        "cursor_batchsize_decimal128_nan",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": DECIMAL128_NAN},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should treat Decimal128 NaN batchSize as 0",
    ),
    CommandTestCase(
        "cursor_batchsize_neg_nan",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": FLOAT_NEGATIVE_NAN},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should treat negative NaN batchSize as 0",
    ),
    CommandTestCase(
        "cursor_batchsize_decimal128_neg_nan",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": DECIMAL128_NEGATIVE_NAN},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should treat Decimal128 negative NaN batchSize as 0",
    ),
]

# Property [Cursor batchSize Large Values]: infinity and very large numeric
# values return all documents in a single batch.
AGGREGATE_CURSOR_BATCHSIZE_LARGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursor_batchsize_infinity",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": FLOAT_INFINITY},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": i} for i in range(5)]),
                "id": Eq(INT64_ZERO),
            },
        },
        msg="aggregate should return all documents for infinity batchSize",
    ),
    CommandTestCase(
        "cursor_batchsize_decimal128_infinity",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": DECIMAL128_INFINITY},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": i} for i in range(5)]),
                "id": Eq(INT64_ZERO),
            },
        },
        msg="aggregate should return all documents for Decimal128 infinity batchSize",
    ),
    CommandTestCase(
        "cursor_batchsize_int64_max",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": INT64_MAX},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": i} for i in range(5)]),
                "id": Eq(INT64_ZERO),
            },
        },
        msg="aggregate should return all documents for Int64 max batchSize",
    ),
    CommandTestCase(
        "cursor_batchsize_double_max",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": DOUBLE_MAX},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": i} for i in range(5)]),
                "id": Eq(INT64_ZERO),
            },
        },
        msg="aggregate should return all documents for DBL_MAX batchSize",
    ),
]

# Property [Cursor Response Size Limit]: the 16MB response size limit reduces
# firstBatch below the requested batchSize when documents are large.
AGGREGATE_CURSOR_RESPONSE_LIMIT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursor_batchsize_16mb_limit",
        docs=[{"_id": i, "data": "x" * 1_000_000} for i in range(20)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": 20},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should reduce firstBatch below batchSize when 16MB limit is reached",
    ),
]

# Property [Cursor Write Stage Behavior]: pipelines ending with $out or $merge
# always produce an empty firstBatch with a closed cursor.
AGGREGATE_CURSOR_WRITE_STAGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursor_batchsize_out_empty",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": "cursor_out_target"}],
            "cursor": {"batchSize": 100},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Eq(INT64_ZERO),
            },
        },
        msg="aggregate should always produce empty firstBatch with $out regardless of batchSize",
    ),
    CommandTestCase(
        "cursor_batchsize_merge_empty",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$merge": {"into": "cursor_merge_target"}}],
            "cursor": {"batchSize": 100},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Eq(INT64_ZERO),
            },
        },
        msg="aggregate should always produce empty firstBatch with $merge regardless of batchSize",
    ),
]

# Property [Cursor Edge Cases]: cursor behavior on empty and non-existent
# collections.
AGGREGATE_CURSOR_EDGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursor_batchsize_zero_empty_collection",
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {"batchSize": 0},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should open a cursor with batchSize 0 even on an empty collection",
    ),
    CommandTestCase(
        "cursor_nonexistent_collection",
        docs=None,
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}},
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Eq(INT64_ZERO),
            },
        },
        msg="aggregate should return empty firstBatch with closed cursor on non-existent coll",
    ),
]

# Property [Cursor Collection-Agnostic Mode]: batchSize controls batching in
# collection-agnostic pipelines.
AGGREGATE_CURSOR_AGNOSTIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cursor_agnostic_batchsize_limits",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"_id": i} for i in range(10)]}],
            "cursor": {"batchSize": 5},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": i} for i in range(5)]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should respect batchSize in collection-agnostic mode",
    ),
    CommandTestCase(
        "cursor_agnostic_batchsize_zero",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"_id": i} for i in range(5)]}],
            "cursor": {"batchSize": 0},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([]),
                "id": Ne(INT64_ZERO),
            },
        },
        msg="aggregate should return empty firstBatch with open cursor for batchSize 0 in agnostic",
    ),
    CommandTestCase(
        "cursor_agnostic_default_batch",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"_id": i} for i in range(5)]}],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {
                "firstBatch": Eq([{"_id": i} for i in range(5)]),
                "id": Eq(INT64_ZERO),
            },
        },
        msg="aggregate should return all documents with default batchSize in agnostic mode",
    ),
]

AGGREGATE_CURSOR_ACCEPTANCE_TESTS = (
    AGGREGATE_CURSOR_DEFAULT_TESTS
    + AGGREGATE_CURSOR_BATCHSIZE_TYPE_TESTS
    + AGGREGATE_CURSOR_BATCHSIZE_ZERO_TESTS
    + AGGREGATE_CURSOR_BATCHSIZE_DOUBLE_TRUNCATION_TESTS
    + AGGREGATE_CURSOR_BATCHSIZE_DECIMAL128_ROUNDING_TESTS
    + AGGREGATE_CURSOR_BATCHSIZE_NAN_TESTS
    + AGGREGATE_CURSOR_BATCHSIZE_LARGE_TESTS
    + AGGREGATE_CURSOR_RESPONSE_LIMIT_TESTS
    + AGGREGATE_CURSOR_WRITE_STAGE_TESTS
    + AGGREGATE_CURSOR_EDGE_TESTS
    + AGGREGATE_CURSOR_AGNOSTIC_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_CURSOR_ACCEPTANCE_TESTS))
def test_aggregate_cursor_acceptance(database_client, collection, test):
    """Test aggregate cursor field acceptance."""
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
