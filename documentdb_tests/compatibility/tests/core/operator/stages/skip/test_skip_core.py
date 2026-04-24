"""Tests for $skip stage core behavior with valid inputs."""

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

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INT64_MAX,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_MAX_FITTING_INT64,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    DOUBLE_ZERO,
    INT32_MAX,
    INT32_OVERFLOW,
    INT64_MAX,
    INT64_ZERO,
)

# Property [Core Behavior]: $skip removes the first N documents from the
# pipeline and passes remaining documents through unmodified, preserving all
# BSON types.
SKIP_CORE_BEHAVIOR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "skip_partial",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        pipeline=[{"$skip": 2}],
        expected=[{"_id": 3, "v": 30}],
        msg="$skip should drop exactly the first N documents",
    ),
    StageTestCase(
        "skip_zero",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$skip": 0}],
        expected=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        msg="$skip 0 should return all documents unchanged",
    ),
    StageTestCase(
        "skip_equals_count",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$skip": 2}],
        expected=[],
        msg="$skip equal to document count should return empty result",
    ),
    StageTestCase(
        "skip_exceeds_count",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$skip": 10_000}],
        expected=[],
        msg="$skip exceeding document count should return empty result",
    ),
    StageTestCase(
        "preserves_bson_types",
        docs=[
            {"_id": 0, "v": "skipped"},
            {
                "_id": 1,
                "str": "hello",
                "int32": 42,
                "int64": Int64(100),
                "double": 3.14,
                "bool": True,
                "null": None,
                "array": [1, 2, 3],
                "obj": {"nested": "value"},
                "oid": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"),
                "dt": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "ts": Timestamp(100, 1),
                "bin": Binary(b"\x01\x02"),
                "dec": DECIMAL128_ONE_AND_HALF,
                "regex": Regex("abc", "i"),
                "code": Code("function(){}"),
                "codews": Code("function(){}", {}),
                "minkey": MinKey(),
                "maxkey": MaxKey(),
            },
        ],
        pipeline=[{"$skip": 1}],
        expected=[
            {
                "_id": 1,
                "str": "hello",
                "int32": 42,
                "int64": Int64(100),
                "double": 3.14,
                "bool": True,
                "null": None,
                "array": [1, 2, 3],
                "obj": {"nested": "value"},
                "oid": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa"),
                "dt": datetime(2024, 1, 1),
                "ts": Timestamp(100, 1),
                "bin": b"\x01\x02",
                "dec": DECIMAL128_ONE_AND_HALF,
                "regex": Regex("abc", 2),
                "code": Code("function(){}"),
                "codews": Code("function(){}", {}),
                "minkey": MinKey(),
                "maxkey": MaxKey(),
            },
        ],
        msg="$skip should preserve all BSON types in passed-through documents",
    ),
]

# Property [Numeric Type Acceptance]: $skip accepts any numeric value that
# represents a non-negative whole number, regardless of BSON numeric type or
# encoding.
SKIP_NUMERIC_TYPE_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "zero_int64",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$skip": INT64_ZERO}],
        expected=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        msg="$skip should accept int64 zero",
    ),
    StageTestCase(
        "zero_double",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$skip": DOUBLE_ZERO}],
        expected=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        msg="$skip should accept double zero",
    ),
    StageTestCase(
        "zero_decimal128",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$skip": DECIMAL128_ZERO}],
        expected=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        msg="$skip should accept Decimal128 zero",
    ),
    StageTestCase(
        "int64_value",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        pipeline=[{"$skip": Int64(2)}],
        expected=[{"_id": 3, "v": 30}],
        msg="$skip should accept int64 values",
    ),
    StageTestCase(
        "whole_double",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        pipeline=[{"$skip": 3.0}],
        expected=[],
        msg="$skip should accept whole-number double values",
    ),
    StageTestCase(
        "decimal128_whole",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        pipeline=[{"$skip": Decimal128("2")}],
        expected=[{"_id": 3, "v": 30}],
        msg="$skip should accept whole-number Decimal128 values",
    ),
    StageTestCase(
        "decimal128_trailing_zeros",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        pipeline=[{"$skip": Decimal128("3.0")}],
        expected=[],
        msg="$skip should accept Decimal128 with trailing zeros",
    ),
    StageTestCase(
        "decimal128_exponent_notation",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        pipeline=[{"$skip": Decimal128("10E-1")}],
        expected=[{"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        msg="$skip should accept Decimal128 with exponent notation",
    ),
    StageTestCase(
        "negative_zero_double",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        pipeline=[{"$skip": DOUBLE_NEGATIVE_ZERO}],
        expected=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        msg="$skip should treat double -0.0 as zero",
    ),
    StageTestCase(
        "negative_zero_decimal128",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        pipeline=[{"$skip": DECIMAL128_NEGATIVE_ZERO}],
        expected=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        msg="$skip should treat Decimal128 -0 as zero",
    ),
    StageTestCase(
        "negative_zero_decimal128_neg_exponent",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        pipeline=[{"$skip": Decimal128("-0E-10")}],
        expected=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        msg="$skip should treat Decimal128 -0E-10 as zero",
    ),
    StageTestCase(
        "negative_zero_decimal128_pos_exponent",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        pipeline=[{"$skip": Decimal128("-0E+10")}],
        expected=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}],
        msg="$skip should treat Decimal128 -0E+10 as zero",
    ),
]

# Property [Integer Boundaries]: $skip accepts whole-number values up to the
# maximum representable 64-bit signed integer across all numeric BSON types.
SKIP_INTEGER_BOUNDARY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "int32_max",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$skip": INT32_MAX}],
        expected=[],
        msg="$skip should accept INT32_MAX",
    ),
    StageTestCase(
        "int64_max",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$skip": INT64_MAX}],
        expected=[],
        msg="$skip should accept INT64_MAX",
    ),
    StageTestCase(
        "double_max_fitting_int64",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$skip": DOUBLE_MAX_FITTING_INT64}],
        expected=[],
        msg="$skip should accept the largest whole-number double fitting in int64",
    ),
    StageTestCase(
        "decimal128_int64_max",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$skip": DECIMAL128_INT64_MAX}],
        expected=[],
        msg="$skip should accept Decimal128 resolving to INT64_MAX",
    ),
    StageTestCase(
        "decimal128_int64_max_exponent",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$skip": Decimal128("9.223372036854775807E18")}],
        expected=[],
        msg="$skip should accept Decimal128 INT64_MAX in exponent notation",
    ),
    StageTestCase(
        "above_int32_max",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$skip": Int64(INT32_OVERFLOW)}],
        expected=[],
        msg="$skip should accept int64 value just above int32 max",
    ),
    StageTestCase(
        "double_2_pow_53",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$skip": float(DOUBLE_MAX_SAFE_INTEGER)}],
        expected=[],
        msg="$skip should accept max safe integer as double",
    ),
    StageTestCase(
        "double_2_pow_53_plus_1_rounds",
        docs=[{"_id": 1, "v": 1}],
        pipeline=[{"$skip": float(DOUBLE_PRECISION_LOSS)}],
        expected=[],
        msg=(
            "$skip should accept float(2^53+1) because IEEE 754 rounds it"
            " to a whole-number double"
        ),
    ),
]

# Property [Consecutive Skip Stages]: Multiple $skip stages in a pipeline are
# additive - each operates on the previous stage's output - and their order
# does not affect the total number of documents skipped.
SKIP_CONSECUTIVE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "two_skips_additive",
        docs=[
            {"_id": 1, "v": 10},
            {"_id": 2, "v": 20},
            {"_id": 3, "v": 30},
            {"_id": 4, "v": 40},
            {"_id": 5, "v": 50},
        ],
        pipeline=[{"$skip": 2}, {"$skip": 1}],
        expected=[{"_id": 4, "v": 40}, {"_id": 5, "v": 50}],
        msg="Two $skip stages should be additive",
    ),
    StageTestCase(
        "three_skips_additive",
        docs=[
            {"_id": 1, "v": 10},
            {"_id": 2, "v": 20},
            {"_id": 3, "v": 30},
            {"_id": 4, "v": 40},
            {"_id": 5, "v": 50},
        ],
        pipeline=[{"$skip": 1}, {"$skip": 1}, {"$skip": 1}],
        expected=[{"_id": 4, "v": 40}, {"_id": 5, "v": 50}],
        msg="Three $skip stages should be additive",
    ),
    StageTestCase(
        "order_does_not_matter",
        docs=[
            {"_id": 1, "v": 10},
            {"_id": 2, "v": 20},
            {"_id": 3, "v": 30},
            {"_id": 4, "v": 40},
            {"_id": 5, "v": 50},
        ],
        pipeline=[{"$skip": 1}, {"$skip": 2}],
        expected=[{"_id": 4, "v": 40}, {"_id": 5, "v": 50}],
        msg="Reversed skip order should produce the same result",
    ),
    StageTestCase(
        "multiple_zero_skips",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$skip": 0}, {"$skip": 0}, {"$skip": 0}],
        expected=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        msg="Multiple zero-valued $skip stages should be no-ops",
    ),
]

# Property [Empty and Non-Existent Collection Success]: Valid skip values
# return an empty result set on both empty and non-existent collections.
SKIP_EMPTY_NONEXISTENT_SUCCESS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "valid_skip_empty_collection",
        docs=[],
        pipeline=[{"$skip": 5}],
        expected=[],
        msg="$skip with valid value on empty collection should return empty result",
    ),
    StageTestCase(
        "valid_skip_nonexistent_collection",
        docs=None,
        pipeline=[{"$skip": 5}],
        expected=[],
        msg="$skip with valid value on non-existent collection should return empty result",
    ),
]

SKIP_SUCCESS_TESTS: list[StageTestCase] = (
    SKIP_CORE_BEHAVIOR_TESTS
    + SKIP_NUMERIC_TYPE_ACCEPTANCE_TESTS
    + SKIP_INTEGER_BOUNDARY_TESTS
    + SKIP_CONSECUTIVE_TESTS
    + SKIP_EMPTY_NONEXISTENT_SUCCESS_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SKIP_SUCCESS_TESTS))
def test_skip_core(collection, test_case: StageTestCase):
    """Test $skip stage behavior for valid inputs."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
