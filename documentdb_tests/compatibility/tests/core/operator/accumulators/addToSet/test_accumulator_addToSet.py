"""Tests for $addToSet accumulator core behavior ($group)."""

from __future__ import annotations

import pytest
from bson import Binary, Regex

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
        "remove_dedup",
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
        "edge_single_null_doc",
        docs=[{"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None]}],
        msg="$addToSet should return [null] for single null document",
    ),
    AccumulatorTestCase(
        "edge_single_missing_doc",
        docs=[{"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": []}],
        msg="$addToSet should return empty array for single document with missing field",
    ),
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
        "edge_array_field_not_traversed",
        docs=[{"v": [5, 1, 8]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[5, 1, 8]]}],
        msg="$addToSet should treat array field as a single element, not traverse it",
    ),
    AccumulatorTestCase(
        "edge_mixed_array_scalar",
        docs=[{"v": 5}, {"v": [5]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [5, [5]]}],
        msg="$addToSet should distinguish scalar 5 from array [5]",
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
    AccumulatorTestCase(
        "edge_expression_mixed_types",
        docs=[{"v": 1}, {"v": "hello"}, {"v": True}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$addToSet": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, "hello", True]}],
        msg="$addToSet should collect mixed-type values from expression",
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
