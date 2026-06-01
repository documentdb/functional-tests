"""Tests for $push accumulator: ordering, duplicates, nested structures, grouping, field paths,
and system variables."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Order Dependence]: the order of elements in the $push output array
# matches the order of documents entering the $group stage.
PUSH_ORDER_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "order_ascending",
        docs=[{"v": 30}, {"v": 10}, {"v": 20}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [10, 20, 30]}],
        msg="$push should produce ascending order when preceded by ascending $sort",
    ),
    AccumulatorTestCase(
        "order_descending",
        docs=[{"v": 30}, {"v": 10}, {"v": 20}],
        pipeline=[
            {"$sort": {"v": -1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [30, 20, 10]}],
        msg="$push should produce descending order when preceded by descending $sort",
    ),
    AccumulatorTestCase(
        "order_multiple_groups",
        docs=[
            {"cat": "A", "v": 3, "s": 1},
            {"cat": "B", "v": 2, "s": 2},
            {"cat": "A", "v": 1, "s": 3},
            {"cat": "B", "v": 4, "s": 4},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": "$cat", "result": {"$push": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": [1, 3]},
            {"_id": "B", "result": [2, 4]},
        ],
        msg="$push should produce independently ordered arrays for each group",
    ),
    AccumulatorTestCase(
        "order_compound_sort",
        docs=[
            {"cat": "A", "v": 2, "p": 10},
            {"cat": "A", "v": 1, "p": 20},
            {"cat": "A", "v": 1, "p": 10},
        ],
        pipeline=[
            {"$sort": {"v": 1, "p": 1}},
            {"$group": {"_id": "$cat", "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": "A", "result": [1, 1, 2]}],
        msg="$push should respect compound sort order within each group",
    ),
    AccumulatorTestCase(
        "order_three_key_mixed_sort",
        docs=[
            {"priority": 1, "status": "open", "ts": 3, "v": "a"},
            {"priority": 1, "status": "open", "ts": 1, "v": "b"},
            {"priority": 1, "status": "closed", "ts": 2, "v": "c"},
            {"priority": 2, "status": "open", "ts": 1, "v": "d"},
            {"priority": 1, "status": "closed", "ts": 5, "v": "e"},
        ],
        pipeline=[
            {"$sort": {"priority": 1, "status": -1, "ts": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": ["b", "a", "c", "e", "d"]}],
        msg="$push should respect 3-key sort with mixed ascending and descending directions",
    ),
    AccumulatorTestCase(
        "order_nested_field_sort",
        docs=[
            {"user": {"dept": "sales"}, "v": 10},
            {"user": {"dept": "eng"}, "v": 20},
            {"user": {"dept": "hr"}, "v": 30},
        ],
        pipeline=[
            {"$sort": {"user.dept": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [20, 30, 10]}],
        msg="$push should respect sort on nested field path",
    ),
]

# Property [Duplicate Handling]: $push preserves all duplicate values in the
# output array, unlike $addToSet which deduplicates.
PUSH_DUPLICATE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "dup_all_same",
        docs=[{"v": 10}, {"v": 10}, {"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [10, 10, 10]}],
        msg="$push should preserve all duplicate values in the array",
    ),
    AccumulatorTestCase(
        "dup_nulls",
        docs=[{"v": None}, {"v": None}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [None, None, None]}],
        msg="$push should preserve duplicate null values",
    ),
    AccumulatorTestCase(
        "dup_objects",
        docs=[{"v": {"a": 1}}, {"v": {"a": 1}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [{"a": 1}, {"a": 1}]}],
        msg="$push should preserve duplicate objects in the array",
    ),
    AccumulatorTestCase(
        "dup_order_preserved",
        docs=[{"v": 10, "s": 1}, {"v": 20, "s": 2}, {"v": 10, "s": 3}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [10, 20, 10]}],
        msg="$push should preserve order of duplicates when sorted",
    ),
]

# Property [Nested Array and Document Handling]: $push collects array and
# document values as-is, creating nested structures.
PUSH_NESTED_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nested_arrays",
        docs=[{"v": [1, 2], "s": 1}, {"v": [3, 4], "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [[1, 2], [3, 4]]}],
        msg="$push should nest array values inside the result array",
    ),
    AccumulatorTestCase(
        "nested_empty_arrays",
        docs=[{"v": [], "s": 1}, {"v": [], "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [[], []]}],
        msg="$push should preserve empty arrays as nested elements",
    ),
    AccumulatorTestCase(
        "nested_mixed_arrays_and_scalars",
        docs=[{"v": [1, 2], "s": 1}, {"v": 3, "s": 2}, {"v": [4], "s": 3}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [[1, 2], 3, [4]]}],
        msg="$push should handle mix of arrays and scalars in output",
    ),
    AccumulatorTestCase(
        "nested_deep_objects",
        docs=[{"v": {"a": {"b": {"c": 1}}}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [{"a": {"b": {"c": 1}}}]}],
        msg="$push should preserve deeply nested objects exactly",
    ),
    AccumulatorTestCase(
        "nested_field_path",
        docs=[{"a": {"b": {"c": 10}}}, {"a": {"b": {"c": 20}}}],
        pipeline=[
            {"$sort": {"a.b.c": 1}},
            {"$group": {"_id": None, "result": {"$push": "$a.b.c"}}},
        ],
        expected=[{"_id": None, "result": [10, 20]}],
        msg="$push should resolve nested field paths to collect leaf values",
    ),
    AccumulatorTestCase(
        "nested_deep_array_of_objects",
        docs=[
            {
                "data": {
                    "users": [
                        {"profile": {"name": "Alice", "scores": [85, 90]}},
                    ],
                },
                "profile": {"name": "bravo"},
            },
            {
                "data": {
                    "users": [
                        {"profile": {"name": "Bob", "scores": [70, 95]}},
                        {"profile": {"name": "Carol", "scores": [88]}},
                    ],
                },
                "profile": {"name": "alpha"},
            },
        ],
        pipeline=[
            {"$sort": {"profile.name": 1}},
            {"$group": {"_id": None, "result": {"$push": "$data"}}},
        ],
        expected=[
            {
                "_id": None,
                "result": [
                    {
                        "users": [
                            {"profile": {"name": "Bob", "scores": [70, 95]}},
                            {"profile": {"name": "Carol", "scores": [88]}},
                        ],
                    },
                    {
                        "users": [
                            {"profile": {"name": "Alice", "scores": [85, 90]}},
                        ],
                    },
                ],
            }
        ],
        msg="$push should preserve deeply nested arrays-of-objects when sorted by nested field",
    ),
]

# Property [Grouping Behavior]: each group produces an independent array, and
# groups with varying sizes produce arrays of corresponding lengths.
PUSH_GROUPING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "group_multiple",
        docs=[
            {"cat": "A", "v": 1},
            {"cat": "B", "v": 2},
            {"cat": "A", "v": 3},
            {"cat": "B", "v": 4},
            {"cat": "B", "v": 5},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": "$cat", "result": {"$push": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": [1, 3]},
            {"_id": "B", "result": [2, 4, 5]},
        ],
        msg="$push should produce independent arrays for each group",
    ),
    AccumulatorTestCase(
        "group_single_doc_per_group",
        docs=[{"cat": "A", "v": 10}, {"cat": "B", "v": 20}, {"cat": "C", "v": 30}],
        pipeline=[
            {"$group": {"_id": "$cat", "result": {"$push": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": [10]},
            {"_id": "B", "result": [20]},
            {"_id": "C", "result": [30]},
        ],
        msg="$push should produce single-element arrays for single-document groups",
    ),
    AccumulatorTestCase(
        "group_large",
        docs=[{"v": i} for i in range(10_000)],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": list(range(10_000))}],
        msg="$push should collect all 10000 values in correct sorted order",
    ),
    AccumulatorTestCase(
        "group_compound_id",
        docs=[
            {"region": "us", "status": "active", "v": 1},
            {"region": "us", "status": "active", "v": 2},
            {"region": "us", "status": "inactive", "v": 3},
            {"region": "eu", "status": "active", "v": 4},
            {"region": "eu", "status": "active", "v": 5},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": {"region": "$region", "status": "$status"},
                    "result": {"$push": "$v"},
                }
            },
            {"$sort": {"_id.region": 1, "_id.status": 1}},
        ],
        expected=[
            {"_id": {"region": "eu", "status": "active"}, "result": [4, 5]},
            {"_id": {"region": "us", "status": "active"}, "result": [1, 2]},
            {"_id": {"region": "us", "status": "inactive"}, "result": [3]},
        ],
        msg="$push should produce independent arrays when grouping by compound _id",
    ),
    AccumulatorTestCase(
        "group_nested_field_id",
        docs=[
            {"user": {"dept": "eng"}, "v": 10},
            {"user": {"dept": "eng"}, "v": 20},
            {"user": {"dept": "sales"}, "v": 30},
            {"user": {"dept": "sales"}, "v": 40},
            {"user": {"dept": "hr"}, "v": 50},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": "$user.dept", "result": {"$push": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "eng", "result": [10, 20]},
            {"_id": "hr", "result": [50]},
            {"_id": "sales", "result": [30, 40]},
        ],
        msg="$push should group correctly when _id is a nested field path",
    ),
    AccumulatorTestCase(
        "group_large_multiple_groups",
        docs=[{"cat": f"g{i % 100}", "v": i} for i in range(10_000)],
        pipeline=[
            {"$group": {"_id": "$cat", "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 1,
                    "count": {"$size": "$result"},
                    "total": {"$sum": "$result"},
                    "lo": {"$min": "$result"},
                    "hi": {"$max": "$result"},
                }
            },
            {
                "$group": {
                    "_id": None,
                    "groups": {"$sum": 1},
                    "total_docs": {"$sum": "$count"},
                    "grand_total": {"$sum": "$total"},
                    "global_lo": {"$min": "$lo"},
                    "global_hi": {"$max": "$hi"},
                }
            },
        ],
        expected=[
            {
                "_id": None,
                "groups": 100,
                "total_docs": 10_000,
                "grand_total": 49_995_000,
                "global_lo": 0,
                "global_hi": 9_999,
            }
        ],
        msg="$push should produce 100 groups with correct content across 10000 documents",
    ),
]

# Property [Field Path Resolution]: $push correctly resolves simple, nested,
# and non-existent field paths.
PUSH_FIELD_PATH_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "field_simple",
        docs=[{"a": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$a"}}},
        ],
        expected=[{"_id": None, "result": [1]}],
        msg="$push should resolve simple field path",
    ),
    AccumulatorTestCase(
        "field_nested",
        docs=[{"a": {"b": 1}}, {"a": {"b": 2}}],
        pipeline=[
            {"$sort": {"a.b": 1}},
            {"$group": {"_id": None, "result": {"$push": "$a.b"}}},
        ],
        expected=[{"_id": None, "result": [1, 2]}],
        msg="$push should resolve nested field path",
    ),
    AccumulatorTestCase(
        "field_nonexistent",
        docs=[{"a": 1}, {"a": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$nonexistent"}}},
        ],
        expected=[{"_id": None, "result": []}],
        msg="$push should produce empty array for non-existent field path",
    ),
    AccumulatorTestCase(
        "field_array_of_objects",
        docs=[{"items": [{"name": "a"}, {"name": "b"}]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$items.name"}}},
        ],
        expected=[{"_id": None, "result": [["a", "b"]]}],
        msg="$push should collect array traversal result from field path through array of objects",
    ),
    AccumulatorTestCase(
        "field_array_index_path",
        docs=[{"a": {"0": {"b": 99}}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$a.0.b"}}},
        ],
        expected=[{"_id": None, "result": [99]}],
        msg="$push should resolve numeric path component as object key in expression context",
    ),
]

# Property [System Variables]: $push accepts system variables as its expression
# argument; $$ROOT collects entire documents.
PUSH_SYSTEM_VARIABLE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "sysvar_root",
        docs=[{"a": 1}, {"a": 2}],
        pipeline=[
            {"$sort": {"a": 1}},
            {"$group": {"_id": None, "result": {"$push": "$$ROOT"}}},
            {"$project": {"_id": 0, "result": {"$map": {"input": "$result", "in": "$$this.a"}}}},
        ],
        expected=[{"result": [1, 2]}],
        msg="$push with $$ROOT should collect entire documents",
    ),
    AccumulatorTestCase(
        "sysvar_current",
        docs=[{"a": 1}, {"a": 2}],
        pipeline=[
            {"$sort": {"a": 1}},
            {"$group": {"_id": None, "result": {"$push": "$$CURRENT"}}},
            {"$project": {"_id": 0, "result": {"$map": {"input": "$result", "in": "$$this.a"}}}},
        ],
        expected=[{"result": [1, 2]}],
        msg="$push with $$CURRENT should collect entire documents like $$ROOT",
    ),
    AccumulatorTestCase(
        "sysvar_root_mixed_shapes",
        docs=[{"a": 1, "s": 1}, {"b": "hello", "s": 2}, {"a": 3, "c": True, "s": 3}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$$ROOT"}}},
            {
                "$project": {
                    "_id": 0,
                    "a_vals": {
                        "$map": {
                            "input": "$result",
                            "in": {"$ifNull": ["$$this.a", "MISSING"]},
                        }
                    },
                    "b_vals": {
                        "$map": {
                            "input": "$result",
                            "in": {"$ifNull": ["$$this.b", "MISSING"]},
                        }
                    },
                    "c_vals": {
                        "$map": {
                            "input": "$result",
                            "in": {"$ifNull": ["$$this.c", "MISSING"]},
                        }
                    },
                }
            },
        ],
        expected=[
            {
                "a_vals": [1, "MISSING", 3],
                "b_vals": ["MISSING", "hello", "MISSING"],
                "c_vals": ["MISSING", "MISSING", True],
            }
        ],
        msg="$push with $$ROOT should preserve documents with different field shapes",
    ),
]

PUSH_CORE_SUCCESS_TESTS = (
    PUSH_ORDER_TESTS
    + PUSH_DUPLICATE_TESTS
    + PUSH_NESTED_TESTS
    + PUSH_GROUPING_TESTS
    + PUSH_FIELD_PATH_TESTS
    + PUSH_SYSTEM_VARIABLE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(PUSH_CORE_SUCCESS_TESTS))
def test_push_core(collection, test_case: AccumulatorTestCase):
    """Test $push core behavior."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
