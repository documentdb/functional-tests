"""Tests for $sum accumulator: constant expressions, expression arguments, and type."""

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
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Constant Expression Behavior]: a numeric constant counts documents
# by multiplying the constant by the group size; a non-numeric constant
# produces 0 (int32); NaN and Infinity constants propagate.
SUM_CONSTANT_EXPRESSION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "constant_int32",
        docs=[{"x": 1}, {"x": 2}, {"x": 3}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": 1}}}],
        expected=3,
        msg="$sum should count documents when given an int32 constant",
    ),
    AccumulatorTestCase(
        "constant_int32_larger",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": 5}}}],
        expected=10,
        msg="$sum should multiply int32 constant by group size",
    ),
    AccumulatorTestCase(
        "constant_non_numeric_true",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": True}}}],
        expected=0,
        msg="$sum should return 0 for non-numeric constant True",
    ),
    AccumulatorTestCase(
        "constant_non_numeric_false",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": False}}}],
        expected=0,
        msg="$sum should return 0 for non-numeric constant False",
    ),
    AccumulatorTestCase(
        "constant_non_numeric_string",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "hello"}}}],
        expected=0,
        msg="$sum should return 0 for non-numeric string constant without $",
    ),
    AccumulatorTestCase(
        "constant_non_numeric_empty_object",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {}}}}],
        expected=0,
        msg="$sum should return 0 for empty object constant",
    ),
    AccumulatorTestCase(
        "constant_non_numeric_non_operator_object",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"a": 1}}}}],
        expected=0,
        msg="$sum should return 0 for non-operator object constant",
    ),
    AccumulatorTestCase(
        "constant_nan_propagates",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": FLOAT_NAN}}}],
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="$sum should propagate NaN constant",
    ),
    AccumulatorTestCase(
        "constant_inf_propagates",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": FLOAT_INFINITY}}}],
        expected=FLOAT_INFINITY,
        msg="$sum should propagate infinity constant",
    ),
    AccumulatorTestCase(
        "constant_neg_inf_propagates",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": FLOAT_NEGATIVE_INFINITY}}}],
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$sum should propagate negative infinity constant",
    ),
]

# Property [Expression Arguments]: $sum accepts any expression that resolves
# to a value; numeric results are summed, non-numeric results are ignored, and
# nested $sum (array summation) is supported.
SUM_EXPRESSION_ARGS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_args_arithmetic_expression",
        docs=[{"a": 3, "b": 2}, {"a": 5, "b": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$add": ["$a", "$b"]}}}}],
        expected=11,
        msg="$sum should accept an arithmetic expression and sum its numeric results",
    ),
    AccumulatorTestCase(
        "expr_args_non_numeric_expression_ignored",
        docs=[{"a": "hello", "b": " world"}, {"a": "foo", "b": "bar"}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$concat": ["$a", "$b"]}}}}],
        expected=0,
        msg="$sum should ignore non-numeric expression results and return 0",
    ),
    AccumulatorTestCase(
        "expr_args_nested_sum_array",
        docs=[{"v": [1, 2, 3]}, {"v": [4, 5]}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$sum": "$v"}}}}],
        expected=15,
        msg="$sum should accept nested $sum (array summation) as its expression",
    ),
]

SUM_CONSTANT_AND_EXPRESSION_TESTS = SUM_CONSTANT_EXPRESSION_TESTS + SUM_EXPRESSION_ARGS_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SUM_CONSTANT_AND_EXPRESSION_TESTS))
def test_accumulator_sum_constants(collection, test_case: AccumulatorTestCase):
    """Test $sum constant expression behavior and expression arguments."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(
        result,
        [{"_id": None, "result": test_case.expected}],
        msg=test_case.msg,
    )


# Property [Constant Type Preservation]: the result type of a numeric constant
# matches the constant's input type.
SUM_CONSTANT_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "constant_type_int32",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": 1}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 2, "type": "int"},
        msg="$sum should preserve int32 type for int32 constant",
    ),
    AccumulatorTestCase(
        "constant_type_int64",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": Int64(1)}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Int64(2), "type": "long"},
        msg="$sum should preserve Int64 type for Int64 constant",
    ),
    AccumulatorTestCase(
        "constant_type_double",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": 2.5}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": 5.0, "type": "double"},
        msg="$sum should preserve double type for double constant",
    ),
    AccumulatorTestCase(
        "constant_type_decimal128",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": Decimal128("3")}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected={"value": Decimal128("6"), "type": "decimal"},
        msg="$sum should preserve Decimal128 type for Decimal128 constant",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUM_CONSTANT_TYPE_TESTS))
def test_accumulator_sum_constant_type(collection, test_case: AccumulatorTestCase):
    """Test $sum constant type preservation."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(
        result,
        [test_case.expected],
        msg=test_case.msg,
    )
