"""Tests for $min accumulator — expression arguments and return type verification ($group)."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

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
