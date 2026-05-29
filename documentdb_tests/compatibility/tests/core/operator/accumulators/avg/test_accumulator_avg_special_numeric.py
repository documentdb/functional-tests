"""
Tests for $avg accumulator special numeric value handling in $group context.

Covers NaN behavior, Infinity behavior, and cross-type interactions
for both double and Decimal128 types.
"""

from __future__ import annotations

import math

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [NaN]: NaN is numeric and produces NaN in the result;
# NaN with Infinity produces NaN; cross-type NaN promotes to Decimal128.
AVG_NAN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_with_finite",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": float("nan")}, {"_id": 2, "v": 30}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": pytest.approx(math.nan, nan_ok=True)}],
        msg="NaN among finite values should produce NaN result",
    ),
    AccumulatorTestCase(
        "all_nan",
        docs=[{"_id": 0, "v": float("nan")}, {"_id": 1, "v": float("nan")}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": pytest.approx(math.nan, nan_ok=True)}],
        msg="All NaN values should return NaN",
    ),
    AccumulatorTestCase(
        "nan_with_infinity",
        docs=[{"_id": 0, "v": float("nan")}, {"_id": 1, "v": FLOAT_INFINITY}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": pytest.approx(math.nan, nan_ok=True)}],
        msg="NaN with Infinity should produce NaN",
    ),
    AccumulatorTestCase(
        "decimal128_nan_with_finite",
        docs=[
            {"_id": 0, "v": Decimal128("10")},
            {"_id": 1, "v": DECIMAL128_NAN},
            {"_id": 2, "v": Decimal128("30")},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DECIMAL128_NAN}],
        msg="Decimal128 NaN among finite values should produce Decimal128 NaN",
    ),
    AccumulatorTestCase(
        "decimal128_nan_with_infinity",
        docs=[{"v": DECIMAL128_NAN}, {"v": DECIMAL128_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("NaN")}],
        msg="Decimal128 NaN with Decimal128 Infinity should produce Decimal128 NaN",
    ),
    AccumulatorTestCase(
        "cross_type_nan",
        docs=[{"_id": 0, "v": float("nan")}, {"_id": 1, "v": Decimal128("5")}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DECIMAL128_NAN}],
        msg="double NaN with Decimal128 should return Decimal128 NaN",
    ),
]

# Property [Infinity]: Infinity with finite values produces Infinity;
# Infinity with -Infinity produces NaN.
AVG_INFINITY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "infinity_with_finite",
        docs=[{"_id": 0, "v": FLOAT_INFINITY}, {"_id": 1, "v": 10}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": FLOAT_INFINITY}],
        msg="Infinity with finite value should produce Infinity",
    ),
    AccumulatorTestCase(
        "negative_infinity_with_finite",
        docs=[{"_id": 0, "v": FLOAT_NEGATIVE_INFINITY}, {"_id": 1, "v": 10}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": FLOAT_NEGATIVE_INFINITY}],
        msg="-Infinity with finite value should produce -Infinity",
    ),
    AccumulatorTestCase(
        "inf_and_neg_inf",
        docs=[{"_id": 0, "v": FLOAT_INFINITY}, {"_id": 1, "v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": pytest.approx(math.nan, nan_ok=True)}],
        msg="Infinity with -Infinity should produce NaN",
    ),
    AccumulatorTestCase(
        "decimal128_infinity_with_finite",
        docs=[{"_id": 0, "v": DECIMAL128_INFINITY}, {"_id": 1, "v": Decimal128("10")}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DECIMAL128_INFINITY}],
        msg="Decimal128 Infinity with finite value should produce Decimal128 Infinity",
    ),
    AccumulatorTestCase(
        "decimal128_neg_infinity_with_finite",
        docs=[{"v": DECIMAL128_NEGATIVE_INFINITY}, {"v": Decimal128("5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": DECIMAL128_NEGATIVE_INFINITY}],
        msg="Decimal128 -Infinity with finite value should produce Decimal128 -Infinity",
    ),
    AccumulatorTestCase(
        "decimal128_inf_and_neg_inf",
        docs=[
            {"_id": 0, "v": DECIMAL128_INFINITY},
            {"_id": 1, "v": DECIMAL128_NEGATIVE_INFINITY},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": DECIMAL128_NAN}],
        msg="Decimal128 Infinity with -Infinity should produce Decimal128 NaN",
    ),
]

AVG_SPECIAL_NUMERIC_TESTS: list[AccumulatorTestCase] = AVG_NAN_TESTS + AVG_INFINITY_TESTS


@pytest.mark.parametrize("test_case", pytest_params(AVG_SPECIAL_NUMERIC_TESTS))
def test_accumulator_avg_special_numeric(collection, test_case: AccumulatorTestCase):
    """Test $avg special numeric value handling in $group context."""
    if test_case.docs:
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
