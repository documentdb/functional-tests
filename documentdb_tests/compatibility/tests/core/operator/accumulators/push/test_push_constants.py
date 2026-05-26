"""Tests for $push accumulator: constant expressions, expression arguments, and object
expression accumulation."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Constant Expression Behavior]: a constant expression is replicated
# once per document in the group, producing an array with one copy per
# document.
PUSH_CONSTANT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "constant_int32",
        docs=[{"x": 1}, {"x": 2}, {"x": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": 1}}},
        ],
        expected=[{"_id": None, "result": [1, 1, 1]}],
        msg="$push should replicate int32 constant once per document",
    ),
    AccumulatorTestCase(
        "constant_int64",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": Int64(99)}}},
        ],
        expected=[{"_id": None, "result": [Int64(99), Int64(99)]}],
        msg="$push should replicate Int64 constant once per document",
    ),
    AccumulatorTestCase(
        "constant_double",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": 2.5}}},
        ],
        expected=[{"_id": None, "result": [2.5, 2.5]}],
        msg="$push should replicate double constant once per document",
    ),
    AccumulatorTestCase(
        "constant_decimal128",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": Decimal128("1.5")}}},
        ],
        expected=[{"_id": None, "result": [Decimal128("1.5"), Decimal128("1.5")]}],
        msg="$push should replicate Decimal128 constant once per document",
    ),
    AccumulatorTestCase(
        "constant_string",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "hello"}}},
        ],
        expected=[{"_id": None, "result": ["hello", "hello"]}],
        msg="$push should replicate string constant (no $) once per document",
    ),
    AccumulatorTestCase(
        "constant_bool_true",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": True}}},
        ],
        expected=[{"_id": None, "result": [True, True]}],
        msg="$push should replicate boolean true constant once per document",
    ),
    AccumulatorTestCase(
        "constant_bool_false",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": False}}},
        ],
        expected=[{"_id": None, "result": [False, False]}],
        msg="$push should replicate boolean false constant once per document",
    ),
    AccumulatorTestCase(
        "constant_null",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": None}}},
        ],
        expected=[{"_id": None, "result": [None, None]}],
        msg="$push should replicate null constant once per document",
    ),
    AccumulatorTestCase(
        "constant_object",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": {"a": 1}}}},
        ],
        expected=[{"_id": None, "result": [{"a": 1}, {"a": 1}]}],
        msg="$push should replicate non-operator object constant once per document",
    ),
    AccumulatorTestCase(
        "constant_empty_object",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": {}}}},
        ],
        expected=[{"_id": None, "result": [{}, {}]}],
        msg="$push should replicate empty object constant once per document",
    ),
]

# Property [Expression Arguments]: $push accepts any expression that resolves
# to a value; the result of the expression is collected into the array.
PUSH_EXPRESSION_ARGS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_arithmetic",
        docs=[{"a": 3, "b": 2}, {"a": 5, "b": 1}],
        pipeline=[
            {"$sort": {"a": 1}},
            {"$group": {"_id": None, "result": {"$push": {"$add": ["$a", "$b"]}}}},
        ],
        expected=[{"_id": None, "result": [5, 6]}],
        msg="$push should accept arithmetic expression and collect computed results",
    ),
    AccumulatorTestCase(
        "expr_concat",
        docs=[
            {"first": "John", "last": "Doe", "s": 1},
            {"first": "Jane", "last": "Smith", "s": 2},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": {"$concat": ["$first", " ", "$last"]}}}},
        ],
        expected=[{"_id": None, "result": ["John Doe", "Jane Smith"]}],
        msg="$push should accept string concatenation expression",
    ),
    AccumulatorTestCase(
        "expr_conditional",
        docs=[{"v": 10, "s": 1}, {"v": 3, "s": 2}, {"v": 8, "s": 3}],
        pipeline=[
            {"$sort": {"s": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$push": {"$cond": [{"$gt": ["$v", 5]}, "high", "low"]}},
                }
            },
        ],
        expected=[{"_id": None, "result": ["high", "low", "high"]}],
        msg="$push should accept conditional expression and collect results",
    ),
    AccumulatorTestCase(
        "expr_ifnull",
        docs=[{"v": 10, "s": 1}, {"v": None, "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": {"$ifNull": ["$v", -1]}}}},
        ],
        expected=[{"_id": None, "result": [10, -1]}],
        msg="$push should accept $ifNull expression with fallback values",
    ),
    AccumulatorTestCase(
        "expr_nested",
        docs=[{"a": 2, "b": 3, "s": 1}, {"a": 4, "b": 5, "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$push": {"$multiply": [{"$add": ["$a", 1]}, "$b"]}},
                }
            },
        ],
        expected=[{"_id": None, "result": [9, 25]}],
        msg="$push should accept nested expression and collect computed results",
    ),
    AccumulatorTestCase(
        "expr_literal_dollar_string",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": {"$literal": "$not_a_field"}}}},
        ],
        expected=[{"_id": None, "result": ["$not_a_field", "$not_a_field"]}],
        msg="$push should collect literal string '$not_a_field' without field resolution",
    ),
    AccumulatorTestCase(
        "expr_type",
        docs=[{"v": 1, "s": 1}, {"v": "hello", "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": {"$type": "$v"}}}},
        ],
        expected=[{"_id": None, "result": ["int", "string"]}],
        msg="$push should collect BSON type strings from $type expression",
    ),
    AccumulatorTestCase(
        "expr_let",
        docs=[{"v": 10, "s": 1}, {"v": 20, "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$push": {"$let": {"vars": {"x": "$v"}, "in": "$$x"}}},
                }
            },
        ],
        expected=[{"_id": None, "result": [10, 20]}],
        msg="$push should accept $let variable expression",
    ),
]

# Property [Object Expression Accumulation]: $push with an object expression
# constructs a subdocument per document, collecting them into an array.
PUSH_OBJECT_EXPR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "obj_expr_basic",
        docs=[
            {"item": "apple", "qty": 5, "s": 1},
            {"item": "banana", "qty": 10, "s": 2},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": {"item": "$item", "qty": "$qty"}}}},
        ],
        expected=[
            {"_id": None, "result": [{"item": "apple", "qty": 5}, {"item": "banana", "qty": 10}]},
        ],
        msg="$push should construct subdocuments from object expression",
    ),
    AccumulatorTestCase(
        "obj_expr_computed",
        docs=[
            {"price": 10, "qty": 2, "s": 1},
            {"price": 5, "qty": 4, "s": 2},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$push": {"total": {"$multiply": ["$price", "$qty"]}}},
                }
            },
        ],
        expected=[
            {"_id": None, "result": [{"total": 20}, {"total": 20}]},
        ],
        msg="$push should construct subdocuments with computed fields",
    ),
    AccumulatorTestCase(
        "obj_expr_missing_fields",
        docs=[
            {"item": "apple", "qty": 5, "s": 1},
            {"item": "banana", "s": 2},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": {"item": "$item", "qty": "$qty"}}}},
        ],
        expected=[
            {"_id": None, "result": [{"item": "apple", "qty": 5}, {"item": "banana"}]},
        ],
        msg="$push should omit missing fields from constructed subdocuments",
    ),
    AccumulatorTestCase(
        "obj_expr_constant_and_field_mix",
        docs=[
            {"item": "apple", "s": 1},
            {"item": "banana", "s": 2},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": {"item": "$item", "source": "store"}}}},
        ],
        expected=[
            {
                "_id": None,
                "result": [
                    {"item": "apple", "source": "store"},
                    {"item": "banana", "source": "store"},
                ],
            },
        ],
        msg="$push should handle mix of constant and field reference in object expression",
    ),
]

PUSH_CONSTANT_AND_EXPRESSION_TESTS = (
    PUSH_CONSTANT_TESTS + PUSH_EXPRESSION_ARGS_TESTS + PUSH_OBJECT_EXPR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(PUSH_CONSTANT_AND_EXPRESSION_TESTS))
def test_push_constants(collection, test_case: AccumulatorTestCase):
    """Test $push constant expressions, expression arguments, and object expression accumulation."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
