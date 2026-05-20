"""Tests for $min accumulator — stage-specific divergence ($group vs $bucketAuto)."""

from __future__ import annotations

import pytest
from bson import Code, Decimal128, Int64, MaxKey, MinKey, Regex

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, MODULO_ZERO_REMAINDER_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_NAN, FLOAT_NAN

# ---------------------------------------------------------------------------
# Property [Tie-Breaking — $group]: when numerically equal values have different
# types, $group preserves the last encountered type.
# ---------------------------------------------------------------------------
MIN_TIE_BREAKING_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "tie_int32_int64_group",
        docs=[{"v": 5}, {"v": Int64(5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "long", "value": Int64(5)}],
        msg="$min in $group should preserve last type (int64) for equal int32 and int64",
    ),
    AccumulatorTestCase(
        "tie_int64_int32_group",
        docs=[{"v": Int64(5)}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "int", "value": 5}],
        msg="$min in $group should preserve last type (int32) for equal int64 and int32",
    ),
    AccumulatorTestCase(
        "tie_double_int32_group",
        docs=[{"v": 5.0}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "int", "value": 5}],
        msg="$min in $group should preserve last type (int32) for equal double and int32",
    ),
    AccumulatorTestCase(
        "tie_decimal_int64_group",
        docs=[{"v": Decimal128("5")}, {"v": Int64(5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "long", "value": Int64(5)}],
        msg="$min in $group should preserve last type (int64) for equal Decimal128 and int64",
    ),
    AccumulatorTestCase(
        "tie_all_four_types_group",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "decimal", "value": Decimal128("5")}],
        msg="$min in $group should preserve last type (Decimal128) for all four equal types",
    ),
    AccumulatorTestCase(
        "tie_reversed_order_group",
        docs=[{"v": Decimal128("5")}, {"v": 5.0}, {"v": Int64(5)}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "int", "value": 5}],
        msg="$min in $group should preserve last type (int32) in reversed order",
    ),
]

# ---------------------------------------------------------------------------
# Property [Tie-Breaking — $bucketAuto]: when numerically equal values have different
# types, $bucketAuto preserves the first encountered type.
# ---------------------------------------------------------------------------
MIN_TIE_BREAKING_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "tie_int32_int64_bucket_auto",
        docs=[{"v": 5}, {"v": Int64(5)}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "int", "value": 5}],
        msg="$min in $bucketAuto should preserve first type (int32) for equal int32 and int64",
    ),
    AccumulatorTestCase(
        "tie_int64_int32_bucket_auto",
        docs=[{"v": Int64(5)}, {"v": 5}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "long", "value": Int64(5)}],
        msg="$min in $bucketAuto should preserve first type (int64) for equal int64 and int32",
    ),
    AccumulatorTestCase(
        "tie_double_int32_bucket_auto",
        docs=[{"v": 5.0}, {"v": 5}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "double", "value": 5.0}],
        msg="$min in $bucketAuto should preserve first type (double) for equal double and int32",
    ),
    AccumulatorTestCase(
        "tie_decimal_int64_bucket_auto",
        docs=[{"v": Decimal128("5")}, {"v": Int64(5)}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "decimal", "value": Decimal128("5")}],
        msg="$min in $bucketAuto should preserve first type (Decimal128) for equal values",
    ),
    AccumulatorTestCase(
        "tie_all_four_types_bucket_auto",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "int", "value": 5}],
        msg="$min in $bucketAuto should preserve first type (int32) for all four equal types",
    ),
    AccumulatorTestCase(
        "tie_reversed_order_bucket_auto",
        docs=[{"v": Decimal128("5")}, {"v": 5.0}, {"v": Int64(5)}, {"v": 5}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "decimal", "value": Decimal128("5")}],
        msg="$min in $bucketAuto should preserve first type (Decimal128) in reversed order",
    ),
]

# ---------------------------------------------------------------------------
# Property [Numeric Equivalence — $group]: numerically equivalent values across
# types are treated as equal. $group: last type wins.
# ---------------------------------------------------------------------------
MIN_NUMERIC_EQUIV_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "equiv_zeros_group",
        docs=[{"v": 0}, {"v": Int64(0)}, {"v": 0.0}, {"v": Decimal128("0")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "decimal", "value": Decimal128("0")}],
        msg="$min in $group should pick last type (Decimal128) for equivalent zeros",
    ),
]

# ---------------------------------------------------------------------------
# Property [Numeric Equivalence — $bucketAuto]: $bucketAuto: first type wins.
# ---------------------------------------------------------------------------
MIN_NUMERIC_EQUIV_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "equiv_zeros_bucket_auto",
        docs=[{"v": 0}, {"v": Int64(0)}, {"v": 0.0}, {"v": Decimal128("0")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}, "value": "$result"}},
        ],
        expected=[{"type": "int", "value": 0}],
        msg="$min in $bucketAuto should pick first type (int32) for equivalent zeros",
    ),
]

# ---------------------------------------------------------------------------
# Property [Negative Zero Tie-Breaking — $group]: $group last-wins for -0.0 vs 0.0.
# ---------------------------------------------------------------------------
MIN_NEGZERO_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negzero_double_group",
        docs=[{"v": -0.0}, {"v": 0.0}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": 0.0}],
        msg="$min in $group should return 0.0 (last wins) for -0.0 vs 0.0",
    ),
    AccumulatorTestCase(
        "negzero_decimal_group",
        docs=[{"v": Decimal128("-0")}, {"v": Decimal128("0")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Decimal128("0")}],
        msg="$min in $group should return Decimal128('0') (last wins) for Decimal128 -0 vs 0",
    ),
]

# ---------------------------------------------------------------------------
# Property [Negative Zero Tie-Breaking — $bucketAuto]: $bucketAuto first-wins.
# ---------------------------------------------------------------------------
MIN_NEGZERO_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negzero_double_bucket_auto",
        docs=[{"v": -0.0}, {"v": 0.0}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": -0.0}],
        msg="$min in $bucketAuto should return -0.0 (first wins) for -0.0 vs 0.0",
    ),
    AccumulatorTestCase(
        "negzero_decimal_bucket_auto",
        docs=[{"v": Decimal128("-0")}, {"v": Decimal128("0")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": Decimal128("-0")}],
        msg="$min in $bucketAuto should return Decimal128('-0') (first wins)",
    ),
]

# ---------------------------------------------------------------------------
# Property [NaN Type Tie-Breaking — $group]: float NaN and Decimal128 NaN tie-break.
# ---------------------------------------------------------------------------
MIN_NAN_TIE_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_float_vs_decimal_group",
        docs=[{"v": FLOAT_NAN}, {"v": DECIMAL128_NAN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "decimal"}],
        msg="$min in $group should preserve Decimal128 NaN type (last wins)",
    ),
]

# ---------------------------------------------------------------------------
# Property [NaN Type Tie-Breaking — $bucketAuto]: first-wins.
# ---------------------------------------------------------------------------
MIN_NAN_TIE_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_float_vs_decimal_bucket_auto",
        docs=[{"v": FLOAT_NAN}, {"v": DECIMAL128_NAN}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            },
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "double"}],
        msg="$min in $bucketAuto should preserve float NaN type (first wins)",
    ),
]

# ---------------------------------------------------------------------------
# Property [Decimal Trailing Zeros — $group]: Decimal128("1.0") vs Decimal128("1.00").
# ---------------------------------------------------------------------------
MIN_DECIMAL_TRAILING_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_trailing_zeros_group",
        docs=[{"v": Decimal128("1.0")}, {"v": Decimal128("1.00")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Decimal128("1.00")}],
        msg="$min in $group should return Decimal128('1.00') (last wins) for trailing zero tie",
    ),
]

# ---------------------------------------------------------------------------
# Property [Decimal Trailing Zeros — $bucketAuto]: first-wins.
# ---------------------------------------------------------------------------
MIN_DECIMAL_TRAILING_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_trailing_zeros_bucket_auto",
        docs=[{"v": Decimal128("1.0")}, {"v": Decimal128("1.00")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": Decimal128("1.0")}],
        msg="$min in $bucketAuto should return Decimal128('1.0') for trailing zero tie",
    ),
]

# ---------------------------------------------------------------------------
# Property [BSON Serialization — $group]: Regex and Code returned correctly in $group.
# ---------------------------------------------------------------------------
MIN_BSON_SERIALIZATION_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_regex_vs_code_group",
        docs=[{"v": Regex("zzz")}, {"v": Code("a")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Regex("zzz")}],
        msg="$min in $group should return Regex as Regex object (Regex < Code)",
    ),
    AccumulatorTestCase(
        "bson_code_vs_maxkey_group",
        docs=[{"v": Code("zzz")}, {"v": MaxKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Code("zzz")}],
        msg="$min in $group should return Code as Code object",
    ),
    AccumulatorTestCase(
        "bson_minkey_vs_maxkey_group",
        docs=[{"v": MinKey()}, {"v": MaxKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": MinKey()}],
        msg="$min in $group should return MinKey directly",
    ),
    AccumulatorTestCase(
        "bson_code_basic_group",
        docs=[{"v": Code("a()")}, {"v": Code("b()")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Code("a()")}],
        msg="$min in $group should return Code as Code object",
    ),
]

# ---------------------------------------------------------------------------
# Property [BSON Serialization — $bucketAuto]: Regex and Code returned correctly
# in $bucketAuto.
# ---------------------------------------------------------------------------
MIN_BSON_SERIALIZATION_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_regex_vs_code_bucket_auto",
        docs=[{"v": Regex("zzz")}, {"v": Code("a")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": Regex("zzz")}],
        msg="$min in $bucketAuto should return Regex as Regex object (Regex < Code)",
    ),
    AccumulatorTestCase(
        "bson_code_vs_maxkey_bucket_auto",
        docs=[{"v": Code("zzz")}, {"v": MaxKey()}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": Code("zzz")}],
        msg="$min in $bucketAuto should return Code as Code object",
    ),
    AccumulatorTestCase(
        "bson_minkey_vs_maxkey_bucket_auto",
        docs=[{"v": MinKey()}, {"v": MaxKey()}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": MinKey()}],
        msg="$min in $bucketAuto should return MinKey directly",
    ),
    AccumulatorTestCase(
        "bson_code_basic_bucket_auto",
        docs=[{"v": Code("a()")}, {"v": Code("b()")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": "$v"}},
                }
            }
        ],
        expected=[{"_id": {"min": 0, "max": 0}, "result": Code("a()")}],
        msg="$min in $bucketAuto should return Code as Code object",
    ),
]

# ---------------------------------------------------------------------------
# Property [Expression Error Codes — $bucketAuto]: $bucketAuto wraps some errors
# with different codes.
# ---------------------------------------------------------------------------
MIN_EXPRESSION_ERROR_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_divide_by_zero_bucket_auto",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": {"$divide": ["$v", 0]}}},
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$min in $bucketAuto should wrap divide-by-zero as BAD_VALUE_ERROR",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero_bucket_auto",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": {"$mod": ["$v", 0]}}},
                }
            }
        ],
        error_code=MODULO_ZERO_REMAINDER_ERROR,
        msg="$min in $bucketAuto should wrap mod-by-zero as MODULO_ZERO_REMAINDER_ERROR",
    ),
]

# ---------------------------------------------------------------------------
# Aggregated success test lists
# ---------------------------------------------------------------------------
MIN_STAGE_DIVERGENCE_GROUP_SUCCESS_TESTS = (
    MIN_TIE_BREAKING_GROUP_TESTS
    + MIN_NUMERIC_EQUIV_GROUP_TESTS
    + MIN_NEGZERO_GROUP_TESTS
    + MIN_NAN_TIE_GROUP_TESTS
    + MIN_DECIMAL_TRAILING_GROUP_TESTS
    + MIN_BSON_SERIALIZATION_GROUP_TESTS
)

MIN_STAGE_DIVERGENCE_BUCKET_AUTO_SUCCESS_TESTS = (
    MIN_TIE_BREAKING_BUCKET_AUTO_TESTS
    + MIN_NUMERIC_EQUIV_BUCKET_AUTO_TESTS
    + MIN_NEGZERO_BUCKET_AUTO_TESTS
    + MIN_NAN_TIE_BUCKET_AUTO_TESTS
    + MIN_DECIMAL_TRAILING_BUCKET_AUTO_TESTS
    + MIN_BSON_SERIALIZATION_BUCKET_AUTO_TESTS
)


# ---------------------------------------------------------------------------
# Test functions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("test_case", pytest_params(MIN_STAGE_DIVERGENCE_GROUP_SUCCESS_TESTS))
def test_accumulator_min_stage_divergence_group(collection, test_case: AccumulatorTestCase):
    """Test $min stage-specific behavior in $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_STAGE_DIVERGENCE_BUCKET_AUTO_SUCCESS_TESTS))
def test_accumulator_min_stage_divergence_bucket_auto(collection, test_case: AccumulatorTestCase):
    """Test $min stage-specific behavior in $bucketAuto."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MIN_EXPRESSION_ERROR_BUCKET_AUTO_TESTS))
def test_accumulator_min_expression_errors_bucket_auto(collection, test_case):
    """Test $min expression error codes in $bucketAuto."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
