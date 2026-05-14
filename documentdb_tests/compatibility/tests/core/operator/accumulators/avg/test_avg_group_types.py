"""
Tests for $avg accumulator type promotion and return type in $group context.

Covers type promotion rules (int32, int64, double, Decimal128), return type
verification via $type, and negative zero normalization.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
)

# Property [Type Promotion]: $avg returns double for integer and double inputs,
# and Decimal128 when any input is Decimal128.
AVG_TYPE_PROMOTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "all_int32",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": 20}, {"_id": 2, "v": 30}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="int32 avg should return double",
    ),
    AccumulatorTestCase(
        "all_int64",
        docs=[
            {"_id": 0, "v": Int64(10)},
            {"_id": 1, "v": Int64(20)},
            {"_id": 2, "v": Int64(30)},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="int64 avg should return double",
    ),
    AccumulatorTestCase(
        "all_double",
        docs=[{"_id": 0, "v": 10.0}, {"_id": 1, "v": 20.0}, {"_id": 2, "v": 30.0}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="double avg should return double",
    ),
    AccumulatorTestCase(
        "all_decimal128",
        docs=[
            {"_id": 0, "v": Decimal128("10")},
            {"_id": 1, "v": Decimal128("20")},
            {"_id": 2, "v": Decimal128("30")},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": Decimal128("20")}],
        msg="decimal128 avg should return decimal128",
    ),
    AccumulatorTestCase(
        "int32_and_int64",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": Int64(20)}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 15.0}],
        msg="int32+int64 avg should return double",
    ),
    AccumulatorTestCase(
        "int32_and_double",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": 20.0}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 15.0}],
        msg="int32+double avg should return double",
    ),
    AccumulatorTestCase(
        "int32_and_decimal128",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": Decimal128("20")}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": Decimal128("15")}],
        msg="int32+decimal128 avg should return decimal128",
    ),
    AccumulatorTestCase(
        "int64_and_decimal128",
        docs=[{"_id": 0, "v": Int64(10)}, {"_id": 1, "v": Decimal128("20")}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": Decimal128("15")}],
        msg="int64+decimal128 avg should return decimal128",
    ),
    AccumulatorTestCase(
        "double_and_decimal128",
        docs=[{"_id": 0, "v": 10.0}, {"_id": 1, "v": Decimal128("20")}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": Decimal128("15")}],
        msg="double+decimal128 avg should return decimal128",
    ),
    AccumulatorTestCase(
        "all_four_types",
        docs=[
            {"_id": 0, "v": 10},
            {"_id": 1, "v": Int64(20)},
            {"_id": 2, "v": 30.0},
            {"_id": 3, "v": Decimal128("40")},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": Decimal128("25")}],
        msg="all four numeric types avg should return decimal128",
    ),
    AccumulatorTestCase(
        "fractional_result_from_int32",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 2}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": 1.5}],
        msg="int32 avg producing fraction should return double",
    ),
]

# Property [Negative Zero]: $avg normalizes negative zero to positive zero
# for both double and Decimal128.
AVG_NEGATIVE_ZERO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "negative_zero_double",
        docs=[
            {"_id": 0, "v": DOUBLE_NEGATIVE_ZERO},
            {"_id": 1, "v": DOUBLE_NEGATIVE_ZERO},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DOUBLE_ZERO}],
        msg="Double -0.0 avg should normalize to 0.0",
    ),
    AccumulatorTestCase(
        "negative_zero_decimal128",
        docs=[
            {"_id": 0, "v": DECIMAL128_NEGATIVE_ZERO},
            {"_id": 1, "v": DECIMAL128_NEGATIVE_ZERO},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DECIMAL128_ZERO}],
        msg="Decimal128 -0 avg should normalize to 0",
    ),
]

# Property [Return Type]: the result is double by default, but Decimal128 if
# any input value is Decimal128.
AVG_RETURN_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_int32_only",
        docs=[{"v": 2}, {"v": 4}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "double"}],
        msg="$avg should return double when all inputs are int32",
    ),
    AccumulatorTestCase(
        "type_int64_only",
        docs=[{"v": Int64(2)}, {"v": Int64(4)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "double"}],
        msg="$avg should return double when all inputs are int64",
    ),
    AccumulatorTestCase(
        "type_int32_int64",
        docs=[{"v": 2}, {"v": Int64(4)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "double"}],
        msg="$avg should return double for int32 and int64 mix",
    ),
    AccumulatorTestCase(
        "type_int32_double",
        docs=[{"v": 2}, {"v": 4.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "double"}],
        msg="$avg should return double for int32 and double mix",
    ),
    AccumulatorTestCase(
        "type_int64_double",
        docs=[{"v": Int64(2)}, {"v": 4.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "double"}],
        msg="$avg should return double for int64 and double mix",
    ),
    AccumulatorTestCase(
        "type_int32_decimal128",
        docs=[{"v": 2}, {"v": Decimal128("4")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "decimal"}],
        msg="$avg should return Decimal128 when any input is Decimal128",
    ),
    AccumulatorTestCase(
        "type_int64_decimal128",
        docs=[{"v": Int64(2)}, {"v": Decimal128("4")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "decimal"}],
        msg="$avg should return Decimal128 for int64 and Decimal128 mix",
    ),
    AccumulatorTestCase(
        "type_double_decimal128",
        docs=[{"v": 2.0}, {"v": Decimal128("4")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "decimal"}],
        msg="$avg should return Decimal128 for double and Decimal128 mix",
    ),
    AccumulatorTestCase(
        "type_decimal128_before_int32",
        docs=[{"v": Decimal128("4")}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "decimal"}],
        msg="$avg should return Decimal128 regardless of document order",
    ),
]

AVG_GROUP_TYPE_TESTS: list[AccumulatorTestCase] = (
    AVG_TYPE_PROMOTION_TESTS + AVG_NEGATIVE_ZERO_TESTS + AVG_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(AVG_GROUP_TYPE_TESTS))
def test_avg_group_types(collection, test_case: AccumulatorTestCase):
    """Test $avg type promotion and return type in $group context."""
    collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)
