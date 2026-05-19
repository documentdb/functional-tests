"""Tests for $max accumulator where $group/$bucket and $bucketAuto produce different results."""

from __future__ import annotations

import math

import pytest
from bson import Code, Decimal128, Int64, MaxKey, MinKey, Regex

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_NAN,
)

# ===========================================================================
# 1. BSON Order Stage Divergence
# ===========================================================================

# Property [BSON Order Stage Divergence]: Code and MaxKey serialization
# differs between $group/$bucket (Code as str, MaxKey wrapped in dict) and
# $bucketAuto (Code as Code object, MaxKey as MaxKey()).
MAX_BSON_ORDER_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_regex_vs_code_group",
        docs=[{"v": Regex("zzz")}, {"v": Code("a")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "a"}],
        msg="$max should pick Code over regex per BSON order (returned as str in $group)",
    ),
    AccumulatorTestCase(
        "bson_code_vs_maxkey_group",
        docs=[{"v": Code("zzz")}, {"v": MaxKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"": MaxKey()}}],
        msg="$max should pick MaxKey over Code per BSON order (wrapped in dict in $group)",
    ),
    AccumulatorTestCase(
        "bson_minkey_vs_maxkey_group",
        docs=[{"v": MinKey()}, {"v": MaxKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"": MaxKey()}}],
        msg="$max should pick MaxKey over MinKey (wrapped in dict in $group)",
    ),
    AccumulatorTestCase(
        "bson_maxkey_before_minkey_group",
        docs=[{"v": MaxKey()}, {"v": MinKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"": MaxKey()}}],
        msg="$max should pick MaxKey even when first (wrapped in dict in $group)",
    ),
]

MAX_BSON_ORDER_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_regex_vs_code_bucket_auto",
        docs=[{"v": Regex("zzz")}, {"v": Code("a")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Code("a")}],
        msg="$max should pick Code over regex per BSON order in $bucketAuto",
    ),
    AccumulatorTestCase(
        "bson_code_vs_maxkey_bucket_auto",
        docs=[{"v": Code("zzz")}, {"v": MaxKey()}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": MaxKey()}],
        msg="$max should pick MaxKey over Code per BSON order in $bucketAuto",
    ),
    AccumulatorTestCase(
        "bson_minkey_vs_maxkey_bucket_auto",
        docs=[{"v": MinKey()}, {"v": MaxKey()}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": MaxKey()}],
        msg="$max should pick MaxKey over MinKey in $bucketAuto",
    ),
    AccumulatorTestCase(
        "bson_maxkey_before_minkey_bucket_auto",
        docs=[{"v": MaxKey()}, {"v": MinKey()}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": MaxKey()}],
        msg="$max should pick MaxKey even when first in $bucketAuto",
    ),
]

# ===========================================================================
# 2. Code Ordering Stage Divergence
# ===========================================================================

# Property [Code Ordering Stage Divergence]: pymongo returns Code without
# scope as str in $group/$bucket but as Code in $bucketAuto.
MAX_CODE_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "code_basic_group",
        docs=[{"v": Code("a()")}, {"v": Code("b()")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "b()"}],
        msg="$max should pick Code with higher string value (returned as str in $group)",
    ),
]

MAX_CODE_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "code_basic_bucket_auto",
        docs=[{"v": Code("a()")}, {"v": Code("b()")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Code("b()")}],
        msg="$max should pick Code with higher string value in $bucketAuto",
    ),
]

# ===========================================================================
# 3. NaN Tie-Breaking Stage Divergence
# ===========================================================================

# Property [NaN Tie-Breaking Stage Divergence]: $group/$bucket return last
# NaN type, $bucketAuto returns first.
MAX_NAN_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_float_vs_decimal_group",
        docs=[{"v": FLOAT_NAN}, {"v": DECIMAL128_NAN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_NAN}],
        msg="$max should return last NaN type (Decimal128 NaN) in $group",
    ),
]

MAX_NAN_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_float_vs_decimal_bucket_auto",
        docs=[{"v": FLOAT_NAN}, {"v": DECIMAL128_NAN}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$max should return first NaN type (float NaN) in $bucketAuto",
    ),
]

# ===========================================================================
# 4. Negative Zero Tie-Breaking Stage Divergence
# ===========================================================================

# Property [Negative Zero Tie-Breaking Stage Divergence]: $group/$bucket
# return last (positive zero), $bucketAuto returns first (negative zero).
MAX_NEGZERO_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negzero_double_group",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}, {"v": DOUBLE_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_ZERO}],
        msg="$max should return last zero (positive) when -0.0 and 0.0 tie in $group",
    ),
    AccumulatorTestCase(
        "negzero_decimal_group",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}, {"v": DECIMAL128_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_ZERO}],
        msg="$max should return last zero (positive) when Decimal128 -0 and 0 tie in $group",
    ),
]

MAX_NEGZERO_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negzero_double_bucket_auto",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}, {"v": DOUBLE_ZERO}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DOUBLE_NEGATIVE_ZERO}],
        msg="$max should return first zero (-0.0) when -0.0 and 0.0 tie in $bucketAuto",
    ),
    AccumulatorTestCase(
        "negzero_decimal_bucket_auto",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}, {"v": DECIMAL128_ZERO}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_NEGATIVE_ZERO}],
        msg="$max should return first zero (Decimal128 -0) when -0 and 0 tie in $bucketAuto",
    ),
]

# ===========================================================================
# 5. Decimal Trailing Zeros Stage Divergence
# ===========================================================================

# Property [Decimal Trailing Zeros Stage Divergence]: $group/$bucket return
# last, $bucketAuto returns first.
MAX_DECIMAL_TRAILING_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_trailing_zeros_group",
        docs=[{"v": Decimal128("1.0")}, {"v": Decimal128("1.00")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("1.00")}],
        msg="$max should return last Decimal128 (1.00) when equal in $group",
    ),
]

MAX_DECIMAL_TRAILING_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_trailing_zeros_bucket_auto",
        docs=[{"v": Decimal128("1.0")}, {"v": Decimal128("1.00")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("1.0")}],
        msg="$max should return first Decimal128 (1.0) when equal in $bucketAuto",
    ),
]

# ===========================================================================
# 6. Tie-Breaking Stage Divergence
# ===========================================================================

# Property [Tie-Breaking Stage Divergence]: when values are numerically equal
# but different types, $group/$bucket preserve the last encountered type while
# $bucketAuto preserves the first.
MAX_TIE_BREAKING_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "tie_int32_int64_group",
        docs=[{"v": 5}, {"v": Int64(5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Int64(5)}],
        msg="$max should preserve type of last equal value (Int64) in $group",
    ),
    AccumulatorTestCase(
        "tie_int64_int32_group",
        docs=[{"v": Int64(5)}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should preserve type of last equal value (int32) in $group",
    ),
    AccumulatorTestCase(
        "tie_double_int32_group",
        docs=[{"v": 5.0}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should preserve type of last equal value (int32) in $group",
    ),
    AccumulatorTestCase(
        "tie_decimal_int64_group",
        docs=[{"v": Decimal128("5")}, {"v": Int64(5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Int64(5)}],
        msg="$max should preserve type of last equal value (Int64) in $group",
    ),
    AccumulatorTestCase(
        "tie_all_four_types_group",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("5")}],
        msg="$max should preserve type of last equal value (Decimal128) in $group",
    ),
    AccumulatorTestCase(
        "tie_reversed_order_group",
        docs=[{"v": Decimal128("5")}, {"v": 5.0}, {"v": Int64(5)}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should preserve type of last equal value (int32) in $group",
    ),
]

MAX_TIE_BREAKING_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "tie_int32_int64_bucket_auto",
        docs=[{"v": 5}, {"v": Int64(5)}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should preserve type of first equal value (int32) in $bucketAuto",
    ),
    AccumulatorTestCase(
        "tie_int64_int32_bucket_auto",
        docs=[{"v": Int64(5)}, {"v": 5}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Int64(5)}],
        msg="$max should preserve type of first equal value (Int64) in $bucketAuto",
    ),
    AccumulatorTestCase(
        "tie_double_int32_bucket_auto",
        docs=[{"v": 5.0}, {"v": 5}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5.0}],
        msg="$max should preserve type of first equal value (double) in $bucketAuto",
    ),
    AccumulatorTestCase(
        "tie_decimal_int64_bucket_auto",
        docs=[{"v": Decimal128("5")}, {"v": Int64(5)}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("5")}],
        msg="$max should preserve type of first equal value (Decimal128) in $bucketAuto",
    ),
    AccumulatorTestCase(
        "tie_all_four_types_bucket_auto",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should preserve type of first equal value (int32) in $bucketAuto",
    ),
    AccumulatorTestCase(
        "tie_reversed_order_bucket_auto",
        docs=[{"v": Decimal128("5")}, {"v": 5.0}, {"v": Int64(5)}, {"v": 5}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("5")}],
        msg="$max should preserve type of first equal value (Decimal128) in $bucketAuto",
    ),
]

# ===========================================================================
# 7. Numeric Equivalence Stage Divergence
# ===========================================================================

# Property [Numeric Equivalence Stage Divergence]: numerically equivalent
# values across types are treated as equal; tie-breaking differs by stage.
MAX_NUMERIC_EQUIV_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "equiv_int_long_double_decimal_group",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("5")}],
        msg="$max should return last type (Decimal128) for equal values in $group",
    ),
    AccumulatorTestCase(
        "equiv_zeros_group",
        docs=[{"v": 0}, {"v": Int64(0)}, {"v": DOUBLE_ZERO}, {"v": DECIMAL128_ZERO}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_ZERO}],
        msg="$max should return last type (Decimal128) for zero values in $group",
    ),
]

MAX_NUMERIC_EQUIV_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "equiv_int_long_double_decimal_bucket_auto",
        docs=[{"v": 5}, {"v": Int64(5)}, {"v": 5.0}, {"v": Decimal128("5")}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should return first type (int32) for equal values in $bucketAuto",
    ),
    AccumulatorTestCase(
        "equiv_zeros_bucket_auto",
        docs=[{"v": 0}, {"v": Int64(0)}, {"v": DOUBLE_ZERO}, {"v": DECIMAL128_ZERO}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 0}],
        msg="$max should return first type (int32) for zero values in $bucketAuto",
    ),
]


# ===========================================================================
# Combined stage divergence tests and test function
# ===========================================================================

MAX_STAGE_DIVERGENCE_TESTS = (
    MAX_BSON_ORDER_GROUP_TESTS
    + MAX_BSON_ORDER_BUCKET_AUTO_TESTS
    + MAX_CODE_GROUP_TESTS
    + MAX_CODE_BUCKET_AUTO_TESTS
    + MAX_NAN_GROUP_TESTS
    + MAX_NAN_BUCKET_AUTO_TESTS
    + MAX_NEGZERO_GROUP_TESTS
    + MAX_NEGZERO_BUCKET_AUTO_TESTS
    + MAX_DECIMAL_TRAILING_GROUP_TESTS
    + MAX_DECIMAL_TRAILING_BUCKET_AUTO_TESTS
    + MAX_TIE_BREAKING_GROUP_TESTS
    + MAX_TIE_BREAKING_BUCKET_AUTO_TESTS
    + MAX_NUMERIC_EQUIV_GROUP_TESTS
    + MAX_NUMERIC_EQUIV_BUCKET_AUTO_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MAX_STAGE_DIVERGENCE_TESTS))
def test_accumulator_max_stage_divergence(collection, test_case: AccumulatorTestCase):
    """Test $max cases where behavior differs between stages."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
