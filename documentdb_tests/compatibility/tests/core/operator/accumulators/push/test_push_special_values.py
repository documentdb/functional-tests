"""Tests for $push accumulator: special numeric value preservation (NaN, Infinity, negative
zero)."""

from __future__ import annotations

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Special Numeric Value Preservation - NaN]: $push preserves NaN
# without normalization.
PUSH_SPECIAL_NAN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "special_float_nan",
        docs=[{"v": FLOAT_NAN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [float("nan")]}],
        msg="$push should preserve float NaN in output array",
    ),
    AccumulatorTestCase(
        "special_decimal128_nan",
        docs=[{"v": DECIMAL128_NAN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [DECIMAL128_NAN]}],
        msg="$push should preserve Decimal128 NaN in output array",
    ),
    AccumulatorTestCase(
        "special_nan_with_finite",
        docs=[{"v": FLOAT_NAN, "s": 1}, {"v": 5.0, "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [float("nan"), 5.0]}],
        msg="$push should preserve NaN alongside finite values in correct position",
    ),
]

# Property [Special Numeric Value Preservation - Infinity]: $push preserves
# Infinity and negative zero without normalization.
PUSH_SPECIAL_NUMERIC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "special_float_inf",
        docs=[{"v": FLOAT_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [FLOAT_INFINITY]}],
        msg="$push should preserve float Infinity in output array",
    ),
    AccumulatorTestCase(
        "special_float_neg_inf",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [FLOAT_NEGATIVE_INFINITY]}],
        msg="$push should preserve float -Infinity in output array",
    ),
    AccumulatorTestCase(
        "special_decimal128_inf",
        docs=[{"v": DECIMAL128_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [DECIMAL128_INFINITY]}],
        msg="$push should preserve Decimal128 Infinity in output array",
    ),
    AccumulatorTestCase(
        "special_decimal128_neg_inf",
        docs=[{"v": DECIMAL128_NEGATIVE_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [DECIMAL128_NEGATIVE_INFINITY]}],
        msg="$push should preserve Decimal128 -Infinity in output array",
    ),
    AccumulatorTestCase(
        "special_negative_zero",
        docs=[{"v": -0.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "result": {"$map": {"input": "$result", "in": {"$toString": "$$this"}}},
                }
            },
        ],
        expected=[{"result": ["-0"]}],
        msg="$push should preserve double -0.0 in output array",
    ),
    AccumulatorTestCase(
        "special_decimal128_neg_zero",
        docs=[{"v": Decimal128("-0")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "result": {"$map": {"input": "$result", "in": {"$toString": "$$this"}}},
                }
            },
        ],
        expected=[{"result": ["-0"]}],
        msg="$push should preserve Decimal128 -0 in output array",
    ),
]

# Property [Special Numeric Value Preservation - Mixed Types]: $push preserves
# special float values when mixed with non-numeric types in the same group.
PUSH_SPECIAL_MIXED_NAN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "special_float_nan_with_non_numeric",
        docs=[
            {"v": FLOAT_NAN, "s": 1},
            {"v": "hello", "s": 2},
            {"v": True, "s": 3},
            {"v": None, "s": 4},
            {"v": {"a": 1}, "s": 5},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [float("nan"), "hello", True, None, {"a": 1}]}],
        msg="$push should preserve float NaN alongside non-numeric types",
    ),
    AccumulatorTestCase(
        "special_decimal128_with_non_numeric",
        docs=[
            {"v": DECIMAL128_NAN, "s": 1},
            {"v": DECIMAL128_INFINITY, "s": 2},
            {"v": DECIMAL128_NEGATIVE_INFINITY, "s": 3},
            {"v": "abc", "s": 4},
            {"v": None, "s": 5},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[
            {
                "_id": None,
                "result": [
                    DECIMAL128_NAN,
                    DECIMAL128_INFINITY,
                    DECIMAL128_NEGATIVE_INFINITY,
                    "abc",
                    None,
                ],
            }
        ],
        msg="$push should preserve Decimal128 special values alongside non-numeric types",
    ),
]

PUSH_SPECIAL_MIXED_NUMERIC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "special_float_inf_with_non_numeric",
        docs=[
            {"v": FLOAT_INFINITY, "s": 1},
            {"v": FLOAT_NEGATIVE_INFINITY, "s": 2},
            {"v": "text", "s": 3},
            {"v": False, "s": 4},
            {"v": [1, 2], "s": 5},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[
            {
                "_id": None,
                "result": [FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY, "text", False, [1, 2]],
            }
        ],
        msg="$push should preserve Infinity values alongside non-numeric types",
    ),
]

PUSH_SPECIAL_VALUES_NAN = PUSH_SPECIAL_NAN_TESTS + PUSH_SPECIAL_MIXED_NAN_TESTS
PUSH_SPECIAL_VALUES = PUSH_SPECIAL_NUMERIC_TESTS + PUSH_SPECIAL_MIXED_NUMERIC_TESTS


@pytest.mark.parametrize("test_case", pytest_params(PUSH_SPECIAL_VALUES))
def test_push_special_values(collection, test_case: AccumulatorTestCase):
    """Test $push special numeric value preservation."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(PUSH_SPECIAL_VALUES_NAN))
def test_push_special_values_nan(collection, test_case: AccumulatorTestCase):
    """Test $push NaN preservation."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccessNaN(result, test_case.expected, msg=test_case.msg)
