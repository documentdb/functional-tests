"""Tests for $max accumulator: input forms, BSON constants, comparison order, type distinction."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
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
        "input_constant_code",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": Code("function(){}")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "function(){}"}],
        msg="$max with Code constant should return Code as string via $group",
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
]


# ===========================================================================
# BSON Comparison Order (Cross-Type)
# ===========================================================================

# Property [BSON Comparison Order]: $max compares values using BSON comparison
# order when documents contain different types.
# BSON order: MinKey < Number < String < Object < Array < Binary < ObjectId
# < Boolean < Date < Timestamp < Regex < Code < MaxKey.
MAX_BSON_ORDER_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_minkey_vs_number",
        docs=[{"v": MinKey()}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should pick number over MinKey per BSON order",
    ),
    AccumulatorTestCase(
        "bson_number_vs_string",
        docs=[{"v": 100}, {"v": "hello"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "hello"}],
        msg="$max should pick string over number per BSON order",
    ),
    AccumulatorTestCase(
        "bson_string_vs_object",
        docs=[{"v": "zzz"}, {"v": {"a": 1}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"a": 1}}],
        msg="$max should pick object over string per BSON order",
    ),
    AccumulatorTestCase(
        "bson_object_vs_array",
        docs=[{"v": {"z": 99}}, {"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1]}],
        msg="$max should pick array over object per BSON order",
    ),
    AccumulatorTestCase(
        "bson_array_vs_binary",
        docs=[{"v": [999]}, {"v": Binary(b"\x00")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": b"\x00"}],
        msg="$max should pick binary over array per BSON order",
    ),
    AccumulatorTestCase(
        "bson_binary_vs_objectid",
        docs=[
            {"v": Binary(b"\xff" * 100)},
            {"v": ObjectId("000000000000000000000001")},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ObjectId("000000000000000000000001")}],
        msg="$max should pick ObjectId over binary per BSON order",
    ),
    AccumulatorTestCase(
        "bson_objectid_vs_boolean",
        docs=[{"v": ObjectId("ffffffffffffffffffffffff")}, {"v": False}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": False}],
        msg="$max should pick boolean over ObjectId per BSON order",
    ),
    AccumulatorTestCase(
        "bson_boolean_vs_datetime",
        docs=[{"v": True}, {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        msg="$max should pick datetime over boolean per BSON order",
    ),
    AccumulatorTestCase(
        "bson_datetime_vs_timestamp",
        docs=[
            {"v": datetime(9999, 12, 31, tzinfo=timezone.utc)},
            {"v": Timestamp(0, 1)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Timestamp(0, 1)}],
        msg="$max should pick timestamp over datetime per BSON order",
    ),
    AccumulatorTestCase(
        "bson_timestamp_vs_regex",
        docs=[{"v": Timestamp(4294967295, 4294967295)}, {"v": Regex("a")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Regex("a")}],
        msg="$max should pick regex over timestamp per BSON order",
    ),
    AccumulatorTestCase(
        "bson_string_over_number",
        docs=[{"v": "a"}, {"v": 999999}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "a"}],
        msg="$max should pick string over number per BSON order",
    ),
]


# ===========================================================================
# BSON Type Distinction
# ===========================================================================

# Property [BSON Type Distinction]: values of different BSON types are
# distinct even when they appear similar (no implicit coercion).
MAX_TYPE_DISTINCTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "distinct_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": False}],
        msg="$max should pick False over 0 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "distinct_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": True}],
        msg="$max should pick True over 1 (boolean > number in BSON order)",
    ),
    AccumulatorTestCase(
        "distinct_numeric_string",
        docs=[{"v": "123"}, {"v": 1000000}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "123"}],
        msg="$max should pick string '123' over int 1000000 (BSON order, no coercion)",
    ),
]


# ===========================================================================
# Combined tests and test function
# ===========================================================================

MAX_INPUT_FORMS_ALL_TESTS = MAX_INPUT_FORM_TESTS + MAX_BSON_ORDER_TESTS + MAX_TYPE_DISTINCTION_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MAX_INPUT_FORMS_ALL_TESTS))
def test_accumulator_max_bson_input_forms(collection, test_case: AccumulatorTestCase):
    """Test $max accumulator input forms, BSON constant types, BSON order, and type distinction."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
