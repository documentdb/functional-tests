"""Tests for $min accumulator: input forms, BSON constants, expression types, and return types."""

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
from documentdb_tests.framework.test_constants import DATE_EPOCH, DATE_Y2K

# ---------------------------------------------------------------------------
# Property [Expression Argument Tests]: $min accumulator accepts various
# expression types as its operand.
# ---------------------------------------------------------------------------
MIN_EXPRESSION_ARGUMENT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "input_field_path",
        docs=[{"v": 10}, {"v": 5}, {"v": 20}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": 5}],
        msg="$min should accept basic field reference",
    ),
    AccumulatorTestCase(
        "input_nested_field",
        docs=[{"a": {"b": 10}}, {"a": {"b": 5}}, {"a": {"b": 20}}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$a.b"}}}],
        expected=[{"_id": None, "result": 5}],
        msg="$min should accept nested document field path",
    ),
    AccumulatorTestCase(
        "input_literal",
        docs=[{"v": 1}, {"v": 2}, {"v": 3}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": 42}}}],
        expected=[{"_id": None, "result": 42}],
        msg="$min should accept constant literal (same for all docs)",
    ),
    AccumulatorTestCase(
        "input_null_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": None}}}],
        expected=[{"_id": None, "result": None}],
        msg="$min should return null when accumulator is null literal",
    ),
    AccumulatorTestCase(
        "input_constant_true",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": True}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": True}],
        msg="$min with boolean True constant should return True",
    ),
    AccumulatorTestCase(
        "input_constant_false",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": False}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": False}],
        msg="$min with boolean False constant should return False",
    ),
    AccumulatorTestCase(
        "input_constant_int64",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": Int64(42)}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Int64(42)}],
        msg="$min with Int64 constant should return that Int64 value",
    ),
    AccumulatorTestCase(
        "input_constant_double",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": 3.14}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 3.14}],
        msg="$min with double constant should return that double value",
    ),
    AccumulatorTestCase(
        "input_constant_decimal128",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": Decimal128("3.14")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("3.14")}],
        msg="$min with Decimal128 constant should return that Decimal128 value",
    ),
    AccumulatorTestCase(
        "input_constant_string",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "hello"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "hello"}],
        msg="$min with string constant (no $) should return that string",
    ),
    AccumulatorTestCase(
        "input_constant_binary",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": Binary(b"\x01\x02")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": b"\x01\x02"}],
        msg="$min with Binary constant should return that Binary value",
    ),
    AccumulatorTestCase(
        "input_constant_objectid",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$min": ObjectId("000000000000000000000000")},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ObjectId("000000000000000000000000")}],
        msg="$min with ObjectId constant should return that ObjectId",
    ),
    AccumulatorTestCase(
        "input_constant_datetime",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$min": datetime(2020, 1, 1, tzinfo=timezone.utc)},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        msg="$min with datetime constant should return that datetime",
    ),
    AccumulatorTestCase(
        "input_constant_timestamp",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": Timestamp(1, 1)}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Timestamp(1, 1)}],
        msg="$min with Timestamp constant should return that Timestamp",
    ),
    AccumulatorTestCase(
        "input_constant_regex",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": Regex("abc", "i")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Regex("abc", "i")}],
        msg="$min with Regex constant should return that Regex",
    ),
    AccumulatorTestCase(
        "input_constant_minkey",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": MinKey()}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"": MinKey()}}],
        msg="$min with MinKey constant should return MinKey wrapped in document",
    ),
    AccumulatorTestCase(
        "input_constant_maxkey",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": MaxKey()}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"": MaxKey()}}],
        msg="$min with MaxKey constant should return MaxKey wrapped in document",
    ),
    AccumulatorTestCase(
        "input_expression_operator",
        docs=[{"v": -10}, {"v": 20}, {"v": -5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": {"$abs": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$min should accept an expression operator as its operand",
    ),
    AccumulatorTestCase(
        "input_expression_multi_arg",
        docs=[{"v": -10, "w": 3}, {"v": 20, "w": 7}, {"v": -5, "w": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$min": {"$add": ["$v", "$w"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": -7}],
        msg="$min should accept a multi-arg expression operator",
    ),
    AccumulatorTestCase(
        "input_expression_nested",
        docs=[{"v": -10}, {"v": 20}, {"v": -5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$min": {"$add": [1, {"$abs": "$v"}]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 6}],
        msg="$min should accept nested expression operators",
    ),
    AccumulatorTestCase(
        "input_sysvar_remove",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$$REMOVE"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$min with $$REMOVE should treat all values as missing and return null",
    ),
    AccumulatorTestCase(
        "input_object_expression",
        docs=[{"v": 10}, {"v": 20}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": {"a": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"a": 5}}],
        msg="$min should accept an object expression and compare resulting objects",
    ),
    AccumulatorTestCase(
        "input_object_expression_with_operator",
        docs=[{"v": -10}, {"v": 20}, {"v": -5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$min": {"a": {"$abs": "$v"}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"a": 5}}],
        msg="$min should accept an object expression containing an operator",
    ),
    AccumulatorTestCase(
        "input_let_expression",
        docs=[{"v": 10}, {"v": 20}, {"v": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$min": {"$let": {"vars": {"x": "$v"}, "in": "$$x"}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$min should accept a $let expression as its operand",
    ),
]

# ---------------------------------------------------------------------------
# Property [Return Type Verification]: $min preserves the BSON type of the minimum value.
# ---------------------------------------------------------------------------
MIN_RETURN_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "return_type_int32",
        docs=[{"v": 10}, {"v": 20}, {"v": 30}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 10, "type": "int"}],
        msg="$min should preserve int32 return type",
    ),
    AccumulatorTestCase(
        "return_type_int64",
        docs=[{"v": Int64(10)}, {"v": Int64(20)}, {"v": Int64(30)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Int64(10), "type": "long"}],
        msg="$min should preserve int64 return type",
    ),
    AccumulatorTestCase(
        "return_type_double",
        docs=[{"v": 1.5}, {"v": 2.5}, {"v": 3.5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 1.5, "type": "double"}],
        msg="$min should preserve double return type",
    ),
    AccumulatorTestCase(
        "return_type_decimal",
        docs=[{"v": Decimal128("1.5")}, {"v": Decimal128("2.5")}, {"v": Decimal128("3.5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Decimal128("1.5"), "type": "decimal"}],
        msg="$min should preserve Decimal128 return type",
    ),
    AccumulatorTestCase(
        "return_type_string",
        docs=[{"v": "apple"}, {"v": "banana"}, {"v": "cherry"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": "apple", "type": "string"}],
        msg="$min should preserve string return type",
    ),
    AccumulatorTestCase(
        "return_type_boolean",
        docs=[{"v": True}, {"v": False}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": False, "type": "bool"}],
        msg="$min should preserve boolean return type",
    ),
    AccumulatorTestCase(
        "return_type_date",
        docs=[{"v": DATE_EPOCH}, {"v": DATE_Y2K}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": DATE_EPOCH, "type": "date"}],
        msg="$min should preserve date return type",
    ),
    AccumulatorTestCase(
        "return_type_null_all",
        docs=[{"v": None}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": None, "type": "null"}],
        msg="$min should return null type when all values are null",
    ),
]


# ---------------------------------------------------------------------------
# Combined success tests
# ---------------------------------------------------------------------------
MIN_GROUP_INPUT_AND_RETURN_SUCCESS_TESTS = MIN_EXPRESSION_ARGUMENT_TESTS + MIN_RETURN_TYPE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MIN_GROUP_INPUT_AND_RETURN_SUCCESS_TESTS))
def test_accumulator_min_group_input_and_return(collection, test_case: AccumulatorTestCase):
    """Test $min accumulator expression arguments and return type verification with $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
