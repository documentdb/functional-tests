"""Tests for $max accumulator: input forms, BSON constants, and expression types."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Input Forms]: $max accumulator accepts various expression types
# as its operand.
MAX_INPUT_FORM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "input_field_path",
        docs=[{"v": 10}, {"v": 20}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 20}],
        msg="$max should accept a basic field path reference",
    ),
    AccumulatorTestCase(
        "input_nested_field",
        docs=[{"a": {"b": 10}}, {"a": {"b": 20}}, {"a": {"b": 5}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$a.b"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 20}],
        msg="$max should accept a nested document field path",
    ),
    AccumulatorTestCase(
        "input_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": 42}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 42}],
        msg="$max with a literal constant should return that constant",
    ),
    AccumulatorTestCase(
        "input_null_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": None}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$max with null literal should return null (all docs produce null)",
    ),
    AccumulatorTestCase(
        "input_constant_true",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": True}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": True}],
        msg="$max with boolean True constant should return True",
    ),
    AccumulatorTestCase(
        "input_constant_false",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": False}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": False}],
        msg="$max with boolean False constant should return False",
    ),
    AccumulatorTestCase(
        "input_constant_int64",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": Int64(42)}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Int64(42)}],
        msg="$max with Int64 constant should return that Int64 value",
    ),
    AccumulatorTestCase(
        "input_constant_double",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": 3.14}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 3.14}],
        msg="$max with double constant should return that double value",
    ),
    AccumulatorTestCase(
        "input_constant_decimal128",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": Decimal128("3.14")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("3.14")}],
        msg="$max with Decimal128 constant should return that Decimal128 value",
    ),
    AccumulatorTestCase(
        "input_constant_string",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "hello"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "hello"}],
        msg="$max with string constant (no $) should return that string",
    ),
    AccumulatorTestCase(
        "input_constant_binary",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": Binary(b"\x01\x02")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": b"\x01\x02"}],
        msg="$max with Binary constant should return that Binary value",
    ),
    AccumulatorTestCase(
        "input_constant_objectid",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": ObjectId("000000000000000000000000")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ObjectId("000000000000000000000000")}],
        msg="$max with ObjectId constant should return that ObjectId",
    ),
    AccumulatorTestCase(
        "input_constant_datetime",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$max": datetime(2020, 1, 1, tzinfo=timezone.utc)},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        msg="$max with datetime constant should return that datetime",
    ),
    AccumulatorTestCase(
        "input_constant_timestamp",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": Timestamp(1, 1)}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Timestamp(1, 1)}],
        msg="$max with Timestamp constant should return that Timestamp",
    ),
    AccumulatorTestCase(
        "input_constant_regex",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": Regex("abc", "i")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Regex("abc", "i")}],
        msg="$max with Regex constant should return that Regex",
    ),
    AccumulatorTestCase(
        "input_constant_minkey",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": MinKey()}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"": MinKey()}}],
        msg="$max with MinKey constant should return MinKey wrapped in document",
    ),
    AccumulatorTestCase(
        "input_constant_maxkey",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": MaxKey()}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"": MaxKey()}}],
        msg="$max with MaxKey constant should return MaxKey wrapped in document",
    ),
    AccumulatorTestCase(
        "input_expression_operator",
        docs=[{"v": -10}, {"v": 20}, {"v": -5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": {"$abs": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 20}],
        msg="$max should accept an expression operator as its operand",
    ),
    AccumulatorTestCase(
        "input_expression_multi_arg",
        docs=[{"v": 10, "w": 3}, {"v": 20, "w": 7}, {"v": 5, "w": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": {"$add": ["$v", "$w"]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 27}],
        msg="$max should accept a multi-arg expression operator",
    ),
    AccumulatorTestCase(
        "input_expression_nested",
        docs=[{"v": -10}, {"v": 20}, {"v": -5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$max": {"$add": [1, {"$abs": "$v"}]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 21}],
        msg="$max should accept nested expression operators",
    ),
    AccumulatorTestCase(
        "input_sysvar_remove",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$$REMOVE"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$max with $$REMOVE should treat all values as missing and return null",
    ),
    AccumulatorTestCase(
        "input_object_expression",
        docs=[{"v": 10}, {"v": 20}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": {"a": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"a": 20}}],
        msg="$max should accept an object expression and compare resulting objects",
    ),
    AccumulatorTestCase(
        "input_object_expression_with_operator",
        docs=[{"v": -10}, {"v": 20}, {"v": -5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": {"a": {"$abs": "$v"}}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"a": 20}}],
        msg="$max should accept an object expression containing an operator",
    ),
    AccumulatorTestCase(
        "input_let_expression",
        docs=[{"v": 10}, {"v": 20}, {"v": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$max": {"$let": {"vars": {"x": "$v"}, "in": "$$x"}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 20}],
        msg="$max should accept a $let expression as its operand",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MAX_INPUT_FORM_TESTS))
def test_accumulator_max_bson_input_forms(collection, test_case: AccumulatorTestCase):
    """Test $max accumulator input forms, BSON constant types, and expression types."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
