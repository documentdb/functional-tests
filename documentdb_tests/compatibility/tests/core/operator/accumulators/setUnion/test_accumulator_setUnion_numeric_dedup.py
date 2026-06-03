"""Tests for $setUnion accumulator: numeric cross-type dedup, zero equivalence, NaN, infinity."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Cross-Type Numeric Deduplication]: values that are numerically
# equal but of different BSON numeric types are deduplicated (e.g., int(1),
# long(1), double(1.0), Decimal128("1") collapse to 1 element).
SETUNION_CROSS_TYPE_NUMERIC_DEDUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "cross_type_int_and_long",
        docs=[{"v": [1]}, {"v": [Int64(1)]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should treat int(1) and long(1) as duplicates",
    ),
    AccumulatorTestCase(
        "cross_type_int_and_double",
        docs=[{"v": [1]}, {"v": [1.0]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should treat int(1) and double(1.0) as duplicates",
    ),
    AccumulatorTestCase(
        "cross_type_int_and_decimal128",
        docs=[{"v": [1]}, {"v": [Decimal128("1")]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should treat int(1) and Decimal128('1') as duplicates",
    ),
    AccumulatorTestCase(
        "cross_type_long_and_double",
        docs=[{"v": [Int64(5)]}, {"v": [5.0]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should treat long(5) and double(5.0) as duplicates",
    ),
    AccumulatorTestCase(
        "cross_type_long_and_decimal128",
        docs=[{"v": [Int64(5)]}, {"v": [Decimal128("5")]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should treat long(5) and Decimal128('5') as duplicates",
    ),
    AccumulatorTestCase(
        "cross_type_double_and_decimal128",
        docs=[{"v": [2.5]}, {"v": [Decimal128("2.5")]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should treat double(2.5) and Decimal128('2.5') as duplicates",
    ),
    AccumulatorTestCase(
        "cross_type_all_four_numeric",
        docs=[
            {"v": [1]},
            {"v": [Int64(1)]},
            {"v": [1.0]},
            {"v": [Decimal128("1")]},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should collapse all four numeric types of value 1 into one element",
    ),
    AccumulatorTestCase(
        "cross_type_negative_values",
        docs=[{"v": [-10]}, {"v": [Int64(-10)]}, {"v": [-10.0]}, {"v": [Decimal128("-10")]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should collapse all four numeric types of value -10 into one element",
    ),
]

# Property [Numeric Type Retention]: when numeric values are deduplicated
# across types, only one remains in the result. The specific type kept is
# implementation-defined, but the count must be 1.
SETUNION_NUMERIC_RETENTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "retention_int_double_count",
        docs=[{"v": [1, 1.0]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should keep only one of int(1) and double(1.0) within same array",
    ),
    AccumulatorTestCase(
        "retention_multiple_equivalent_values",
        docs=[{"v": [1, 2, 3]}, {"v": [Int64(1), Int64(2), Int64(3)]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should collapse int and long versions to 3 unique elements",
    ),
]

# Property [Zero Equivalence]: int(0), long(0), double(0.0), and
# Decimal128("0") are numerically equivalent and collapse to 1 element.
SETUNION_ZERO_EQUIVALENCE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "zero_int_and_double",
        docs=[{"v": [0]}, {"v": [0.0]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should treat int(0) and double(0.0) as the same zero",
    ),
    AccumulatorTestCase(
        "zero_all_four_types",
        docs=[
            {"v": [0]},
            {"v": [Int64(0)]},
            {"v": [0.0]},
            {"v": [Decimal128("0")]},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should collapse all four numeric zero types to one element",
    ),
]

# Property [Negative Zero as Array Element]: negative zero is treated as
# equal to positive zero for deduplication purposes.
SETUNION_NEGATIVE_ZERO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "neg_zero_double_equiv",
        docs=[{"v": [0.0]}, {"v": [DOUBLE_NEGATIVE_ZERO]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should treat double(0.0) and double(-0.0) as equivalent",
    ),
    AccumulatorTestCase(
        "neg_zero_decimal128_equiv",
        docs=[{"v": [Decimal128("0")]}, {"v": [DECIMAL128_NEGATIVE_ZERO]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should treat Decimal128('0') and Decimal128('-0') as equivalent",
    ),
    AccumulatorTestCase(
        "neg_zero_cross_type_equiv",
        docs=[
            {"v": [0]},
            {"v": [DOUBLE_NEGATIVE_ZERO]},
            {"v": [DECIMAL128_NEGATIVE_ZERO]},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should collapse int(0), double(-0.0), Decimal128('-0') to one element",
    ),
]

# Property [NaN Deduplication]: NaN values are equal to each other for
# deduplication, regardless of numeric type. NaN is distinct from all
# non-NaN values.
SETUNION_NAN_DEDUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_double_dedup",
        docs=[{"v": [FLOAT_NAN]}, {"v": [FLOAT_NAN]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should deduplicate double NaN values",
    ),
    AccumulatorTestCase(
        "nan_decimal128_dedup",
        docs=[{"v": [Decimal128("NaN")]}, {"v": [Decimal128("NaN")]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should deduplicate Decimal128 NaN values",
    ),
    AccumulatorTestCase(
        "nan_cross_type_dedup",
        docs=[{"v": [FLOAT_NAN]}, {"v": [Decimal128("NaN")]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should treat double NaN and Decimal128 NaN as equivalent",
    ),
    AccumulatorTestCase(
        "nan_distinct_from_zero",
        docs=[{"v": [FLOAT_NAN]}, {"v": [0]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat NaN and 0 as distinct",
    ),
    AccumulatorTestCase(
        "nan_distinct_from_infinity",
        docs=[{"v": [FLOAT_NAN]}, {"v": [FLOAT_INFINITY]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat NaN and Infinity as distinct",
    ),
]

# Property [Infinity Deduplication]: Infinity values are compared by sign and
# type equivalence across numeric types.
SETUNION_INFINITY_DEDUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "inf_double_dedup",
        docs=[{"v": [FLOAT_INFINITY]}, {"v": [FLOAT_INFINITY]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should deduplicate double Infinity values",
    ),
    AccumulatorTestCase(
        "neg_inf_double_dedup",
        docs=[{"v": [FLOAT_NEGATIVE_INFINITY]}, {"v": [FLOAT_NEGATIVE_INFINITY]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should deduplicate double negative Infinity values",
    ),
    AccumulatorTestCase(
        "inf_and_neg_inf_distinct",
        docs=[{"v": [FLOAT_INFINITY]}, {"v": [FLOAT_NEGATIVE_INFINITY]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat Infinity and -Infinity as distinct",
    ),
    AccumulatorTestCase(
        "inf_cross_type_double_decimal128_dedup",
        docs=[{"v": [FLOAT_INFINITY]}, {"v": [Decimal128("Infinity")]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should treat double Infinity and Decimal128 Infinity as equivalent",
    ),
    AccumulatorTestCase(
        "neg_inf_cross_type_double_decimal128_dedup",
        docs=[{"v": [FLOAT_NEGATIVE_INFINITY]}, {"v": [Decimal128("-Infinity")]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should treat double -Infinity and Decimal128 -Infinity as equivalent",
    ),
    AccumulatorTestCase(
        "inf_distinct_from_large_number",
        docs=[{"v": [FLOAT_INFINITY]}, {"v": [1e308]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat Infinity and large finite number as distinct",
    ),
]

# Property [Numeric Boundary Deduplication]: numeric type equivalence holds at
# boundary values; values that cannot be exactly represented across types are
# treated as distinct.
SETUNION_NUMERIC_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "boundary_int32_max_as_int64",
        docs=[{"v": [2_147_483_647]}, {"v": [Int64(2_147_483_647)]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should collapse int32 max with equivalent Int64",
    ),
    AccumulatorTestCase(
        "boundary_large_exact_int64_double",
        docs=[{"v": [Int64(2**53)]}, {"v": [float(2**53)]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 1}],
        msg="$setUnion should collapse Int64 and exact double at 2^53",
    ),
    AccumulatorTestCase(
        "boundary_large_inexact_int64_double",
        docs=[{"v": [Int64(2**53 + 1)]}, {"v": [float(2**53 + 1)]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat Int64 and inexact double as distinct at 2^53+1",
    ),
]

SETUNION_NUMERIC_DEDUP_TESTS = (
    SETUNION_CROSS_TYPE_NUMERIC_DEDUP_TESTS
    + SETUNION_NUMERIC_RETENTION_TESTS
    + SETUNION_ZERO_EQUIVALENCE_TESTS
    + SETUNION_NEGATIVE_ZERO_TESTS
    + SETUNION_NAN_DEDUP_TESTS
    + SETUNION_INFINITY_DEDUP_TESTS
    + SETUNION_NUMERIC_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_NUMERIC_DEDUP_TESTS))
def test_accumulator_setUnion_numeric_dedup(collection, test_case: AccumulatorTestCase):
    """Test $setUnion accumulator numeric cross-type deduplication."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
