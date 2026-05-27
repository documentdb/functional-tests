"""Tests for $addToSet accumulator core behavior ($group)."""

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

# ---------------------------------------------------------------------------
# Property lists
# ---------------------------------------------------------------------------

# Property [$$REMOVE Excluded]: $$REMOVE via $cond is treated as missing.
ADDTOSET_REMOVE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "remove_all",
        docs=[{"v": -1}, {"v": -2}, {"v": -3}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"$cond": [{"$gte": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": []}],
        msg="$addToSet should treat $$REMOVE as missing and return empty array",
    ),
    AccumulatorTestCase(
        "remove_some",
        docs=[{"v": -1}, {"v": 5}, {"v": -2}, {"v": 10}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"$cond": [{"$gte": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [5, 10]}],
        msg="$addToSet should exclude $$REMOVE values and collect the rest",
    ),
    AccumulatorTestCase(
        "remove_and_null_value",
        docs=[{"v": 1}, {"v": 2}, {"v": 3}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"$cond": [{"$gt": ["$v", 2]}, None, "$$REMOVE"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should collect null produced by $cond while excluding $$REMOVE",
    ),
    AccumulatorTestCase(
        "remove_with_duplicate_values",
        docs=[{"v": 5}, {"v": 5}, {"v": -1}, {"v": -2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"$cond": [{"$gte": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [5]}],
        msg="$addToSet should deduplicate values and exclude $$REMOVE entries",
    ),
]

# Property [$$REMOVE Interaction with Deduplication]: $$REMOVE entries are excluded and
# remaining values are properly deduplicated.
ADDTOSET_REMOVE_DEDUP_INTERACTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "remove_dedup_same_value_produced",
        docs=[{"v": 1}, {"v": 2}, {"v": -1}, {"v": -2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"$cond": [{"$gte": ["$v", 0]}, "kept", "$$REMOVE"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["kept"]}],
        msg="$addToSet should collect single value when $cond produces same value "
        "for multiple docs and $$REMOVE for others",
    ),
]

# Property [Unique Value Collection]: $addToSet returns an array of all unique values.
ADDTOSET_UNIQUE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "unique_distinct",
        docs=[{"v": 10}, {"v": 20}, {"v": 30}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, 20, 30]}],
        msg="$addToSet should return all distinct values",
    ),
    AccumulatorTestCase(
        "unique_with_duplicates",
        docs=[{"v": 10}, {"v": 20}, {"v": 10}, {"v": 30}, {"v": 20}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, 20, 30]}],
        msg="$addToSet should deduplicate repeated values",
    ),
    AccumulatorTestCase(
        "unique_all_same",
        docs=[{"v": 42}, {"v": 42}, {"v": 42}, {"v": 42}, {"v": 42}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [42]}],
        msg="$addToSet should collapse identical values into one element",
    ),
    AccumulatorTestCase(
        "unique_single_doc",
        docs=[{"v": 7}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [7]}],
        msg="$addToSet should return single-element array for one document",
    ),
]

# Property [Array as Single Element]: array values are appended as a single element, not unwound.
ADDTOSET_ARRAY_ELEMENT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "array_distinct",
        docs=[{"v": [1, 2]}, {"v": [3, 4]}, {"v": [1, 2]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[1, 2], [3, 4]]}],
        msg="$addToSet should treat arrays as single elements and deduplicate identical arrays",
    ),
    AccumulatorTestCase(
        "array_empty",
        docs=[{"v": []}, {"v": []}, {"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[], [1]]}],
        msg="$addToSet should treat empty arrays as single elements and deduplicate them",
    ),
    AccumulatorTestCase(
        "array_nested",
        docs=[{"v": [[1]]}, {"v": [[2]]}, {"v": [[1]]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[[1]], [[2]]]}],
        msg="$addToSet should treat nested arrays as single elements and deduplicate them",
    ),
    AccumulatorTestCase(
        "array_mixed_scalar",
        docs=[{"v": 1}, {"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, [1]]}],
        msg="$addToSet should distinguish scalar 1 from array [1]",
    ),
    AccumulatorTestCase(
        "array_single_doc",
        docs=[{"v": [1, 2, 3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[1, 2, 3]]}],
        msg="$addToSet should wrap the array value as a single element in the result",
    ),
]

# Property [Expression Arguments]: $addToSet accepts various expression forms.
ADDTOSET_EXPRESSION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_field_path",
        docs=[{"v": 10}, {"v": 20}, {"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, 20]}],
        msg="$addToSet should collect values from a field path expression",
    ),
    AccumulatorTestCase(
        "expr_nested_field",
        docs=[{"a": {"b": 1}}, {"a": {"b": 2}}, {"a": {"b": 1}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$a.b"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, 2]}],
        msg="$addToSet should collect values from a nested field path",
    ),
    AccumulatorTestCase(
        "expr_literal",
        docs=[{"v": 1}, {"v": 2}, {"v": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": 42}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [42]}],
        msg="$addToSet should deduplicate a constant literal applied to all docs",
    ),
    AccumulatorTestCase(
        "expr_computed",
        docs=[{"price": 10, "qty": 2}, {"price": 5, "qty": 3}, {"price": 10, "qty": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": {"$multiply": ["$price", "$qty"]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [20, 15]}],
        msg="$addToSet should collect unique computed expression results",
    ),
    AccumulatorTestCase(
        "expr_null_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": None}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should collect null literal and deduplicate across docs",
    ),
    AccumulatorTestCase(
        "expr_composite_array_path",
        docs=[{"a": [{"b": 1}, {"b": 2}]}, {"a": [{"b": 3}, {"b": 1}]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$a.b"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[3, 1], [1, 2]]}],
        msg="$addToSet should collect array values from composite array path",
    ),
]

# Property [Grouping by Key]: groups compute independently.
ADDTOSET_GROUPING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multi_group",
        docs=[
            {"g": "A", "v": 1},
            {"g": "A", "v": 2},
            {"g": "A", "v": 1},
            {"g": "B", "v": 3},
            {"g": "B", "v": 3},
            {"g": "B", "v": 4},
        ],
        pipeline=[
            {"$group": {"_id": "$g", "result": {"$addToSet": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": [1, 2]},
            {"_id": "B", "result": [3, 4]},
        ],
        msg="$addToSet should compute unique sets independently per group key",
    ),
]

# Property [Empty Collection]: $group on empty collection produces no output.
ADDTOSET_EMPTY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "empty_collection",
        docs=None,
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[],
        msg="$addToSet should produce no output documents for an empty collection",
    ),
]

# Property [Edge Cases]: accumulator-specific edge cases.
ADDTOSET_EDGE_CASE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "edge_many_unique",
        docs=[{"v": i} for i in range(100)],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": list(range(100))}],
        msg="$addToSet should collect 100 unique values into a 100-element array",
    ),
    AccumulatorTestCase(
        "edge_many_docs_few_unique",
        docs=[{"v": i % 5} for i in range(100)],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [0, 1, 2, 3, 4]}],
        msg="$addToSet should deduplicate 100 docs down to 5 unique values",
    ),
    AccumulatorTestCase(
        "edge_array_not_unwound",
        docs=[{"v": [5, 1, 8]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[5, 1, 8]]}],
        msg="$addToSet should treat array field as a single element, not traverse it",
    ),
    AccumulatorTestCase(
        "edge_binary_different_subtypes",
        docs=[{"v": Binary(b"\x00", 0)}, {"v": Binary(b"\x00", 5)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [b"\x00", Binary(b"\x00", 5)]}],
        msg="$addToSet should treat Binary values with different subtypes as distinct",
    ),
    AccumulatorTestCase(
        "edge_regex_different_flags",
        docs=[{"v": Regex("abc", "i")}, {"v": Regex("abc", "m")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Regex("abc", "i"), Regex("abc", "m")]}],
        msg="$addToSet should treat Regex values with different flags as distinct",
    ),
]

# ---------------------------------------------------------------------------
# Property [BSON Constant Arguments]: $addToSet accepts BSON constants as the
# accumulator argument. Since every doc yields the same constant, the result
# set contains exactly one element.
# ---------------------------------------------------------------------------
ADDTOSET_BSON_CONSTANT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "const_true",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": True}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [True]}],
        msg="$addToSet with boolean True constant should return [True]",
    ),
    AccumulatorTestCase(
        "const_false",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": False}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [False]}],
        msg="$addToSet with boolean False constant should return [False]",
    ),
    AccumulatorTestCase(
        "const_int64",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": Int64(42)}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Int64(42)]}],
        msg="$addToSet with Int64 constant should return single-element set",
    ),
    AccumulatorTestCase(
        "const_double",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": 3.14}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [3.14]}],
        msg="$addToSet with double constant should return single-element set",
    ),
    AccumulatorTestCase(
        "const_decimal128",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": Decimal128("3.14")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Decimal128("3.14")]}],
        msg="$addToSet with Decimal128 constant should return single-element set",
    ),
    AccumulatorTestCase(
        "const_string",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "hello"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["hello"]}],
        msg="$addToSet with string constant should return single-element set",
    ),
    AccumulatorTestCase(
        "const_binary",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": Binary(b"\x01\x02")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [b"\x01\x02"]}],
        msg="$addToSet with Binary constant should return single-element set",
    ),
    AccumulatorTestCase(
        "const_objectid",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": ObjectId("000000000000000000000000")},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [ObjectId("000000000000000000000000")]}],
        msg="$addToSet with ObjectId constant should return single-element set",
    ),
    AccumulatorTestCase(
        "const_datetime",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": datetime(2020, 1, 1, tzinfo=timezone.utc)},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [datetime(2020, 1, 1, tzinfo=timezone.utc)]}],
        msg="$addToSet with datetime constant should return single-element set",
    ),
    AccumulatorTestCase(
        "const_timestamp",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": Timestamp(1, 1)}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Timestamp(1, 1)]}],
        msg="$addToSet with Timestamp constant should return single-element set",
    ),
    AccumulatorTestCase(
        "const_regex",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": Regex("abc", "i")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [Regex("abc", "i")]}],
        msg="$addToSet with Regex constant should return single-element set",
    ),
    AccumulatorTestCase(
        "const_null",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": None}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet with null constant should return [null]",
    ),
    AccumulatorTestCase(
        "const_minkey",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": MinKey()}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"": MinKey()}]}],
        msg="$addToSet with MinKey constant should return MinKey wrapped in document",
    ),
    AccumulatorTestCase(
        "const_maxkey",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": MaxKey()}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"": MaxKey()}]}],
        msg="$addToSet with MaxKey constant should return MaxKey wrapped in document",
    ),
]

# ---------------------------------------------------------------------------
# Property [Expression Types]: $addToSet accepts various expression types as
# its operand and evaluates them per document before collecting unique values.
# ---------------------------------------------------------------------------
ADDTOSET_EXPRESSION_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_type_operator_single",
        docs=[{"v": -10}, {"v": 20}, {"v": -5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": {"$abs": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, 20, 5]}],
        msg="$addToSet should accept single-input expression operator",
    ),
    AccumulatorTestCase(
        "expr_type_operator_multi_arg",
        docs=[{"v": -10, "w": 3}, {"v": 20, "w": 7}, {"v": -5, "w": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"$add": ["$v", "$w"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [-7, 27, -4]}],
        msg="$addToSet should accept a multi-arg expression operator",
    ),
    AccumulatorTestCase(
        "expr_type_nested",
        docs=[{"v": -10}, {"v": 20}, {"v": -5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"$add": [1, {"$abs": "$v"}]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [11, 21, 6]}],
        msg="$addToSet should accept nested expression operators",
    ),
    AccumulatorTestCase(
        "expr_type_sysvar_remove",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$$REMOVE"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": []}],
        msg="$addToSet with $$REMOVE should exclude all values and return empty array",
    ),
    AccumulatorTestCase(
        "expr_type_object_expression",
        docs=[{"v": 10}, {"v": 20}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": {"a": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": 10}, {"a": 20}, {"a": 5}]}],
        msg="$addToSet should accept an object expression",
    ),
    AccumulatorTestCase(
        "expr_type_object_with_operator",
        docs=[{"v": -10}, {"v": 20}, {"v": -5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"a": {"$abs": "$v"}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [{"a": 10}, {"a": 20}, {"a": 5}]}],
        msg="$addToSet should accept an object expression containing an operator",
    ),
    AccumulatorTestCase(
        "expr_type_let",
        docs=[{"v": 10}, {"v": 20}, {"v": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$addToSet": {"$let": {"vars": {"x": "$v"}, "in": "$$x"}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, 20, 5]}],
        msg="$addToSet should accept a $let expression as its operand",
    ),
]

# ---------------------------------------------------------------------------
# Property [Order Independence]: $addToSet produces the same set regardless
# of input order.
# ---------------------------------------------------------------------------
ADDTOSET_ORDER_INDEPENDENCE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "order_independent_asc",
        docs=[{"v": 3}, {"v": 1}, {"v": 5}, {"v": 2}, {"v": 4}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, 2, 3, 4, 5]}],
        msg="$addToSet with ascending sort should produce same set",
    ),
    AccumulatorTestCase(
        "order_independent_desc",
        docs=[{"v": 3}, {"v": 1}, {"v": 5}, {"v": 2}, {"v": 4}],
        pipeline=[
            {"$sort": {"v": -1}},
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, 2, 3, 4, 5]}],
        msg="$addToSet with descending sort should produce same set",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

ADDTOSET_SUCCESS_TESTS = (
    ADDTOSET_REMOVE_TESTS
    + ADDTOSET_REMOVE_DEDUP_INTERACTION_TESTS
    + ADDTOSET_UNIQUE_TESTS
    + ADDTOSET_ARRAY_ELEMENT_TESTS
    + ADDTOSET_EXPRESSION_TESTS
    + ADDTOSET_GROUPING_TESTS
    + ADDTOSET_EMPTY_TESTS
    + ADDTOSET_EDGE_CASE_TESTS
    + ADDTOSET_BSON_CONSTANT_TESTS
    + ADDTOSET_EXPRESSION_TYPE_TESTS
    + ADDTOSET_ORDER_INDEPENDENCE_TESTS
)

# ---------------------------------------------------------------------------
# Test function
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_SUCCESS_TESTS))
def test_accumulator_addToSet(collection, test_case: AccumulatorTestCase):
    """Test $addToSet accumulator success cases with $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_order_in=["result"])


# ---------------------------------------------------------------------------
# Property-specific tests
# ---------------------------------------------------------------------------

# Property [Return Type]: $addToSet always returns an array type.
ADDTOSET_RETURN_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "return_type_numeric",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": [1, 2], "type": "array"}],
        msg="$addToSet should return array type for numeric inputs",
    ),
    AccumulatorTestCase(
        "return_type_string",
        docs=[{"v": "a"}, {"v": "b"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": ["a", "b"], "type": "array"}],
        msg="$addToSet should return array type for string inputs",
    ),
    AccumulatorTestCase(
        "return_type_null_only",
        docs=[{"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": [None], "type": "array"}],
        msg="$addToSet should return array type for null-only inputs",
    ),
    AccumulatorTestCase(
        "return_type_missing_only",
        docs=[{"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": [], "type": "array"}],
        msg="$addToSet should return array type for all-missing inputs",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_RETURN_TYPE_TESTS))
def test_accumulator_addToSet_return_type(collection, test_case: AccumulatorTestCase):
    """Test $addToSet return type verification."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_order_in=["value"])
