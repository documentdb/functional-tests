"""Tests for $setUnion accumulator: missing field handling, $$REMOVE, and null elements."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Missing Field Ignored]: missing fields are silently ignored in
# accumulator context, producing empty array when no array values remain.
SETUNION_MISSING_FIELD_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "missing_single_doc",
        docs=[{"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        expected=[{"_id": None, "result": []}],
        msg="$setUnion should return empty array when the only document is missing the field",
    ),
    AccumulatorTestCase(
        "missing_all_docs",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        expected=[{"_id": None, "result": []}],
        msg="$setUnion should return empty array when all documents are missing the field",
    ),
    AccumulatorTestCase(
        "missing_mixed_with_array",
        docs=[{"v": [1, 2]}, {"x": 1}, {"v": [2, 3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should ignore missing fields and union only array values",
    ),
    AccumulatorTestCase(
        "missing_minority_docs",
        docs=[
            {"v": [1, 2]},
            {"x": 1},
            {"v": [3, 4]},
            {"x": 2},
            {"v": [4, 5]},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3, 4, 5]}],
        msg="$setUnion should skip missing docs and union the 3 arrays",
    ),
    AccumulatorTestCase(
        "missing_majority_docs",
        docs=[
            {"x": 1},
            {"x": 2},
            {"v": [10, 20]},
            {"x": 3},
            {"x": 4},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [10, 20]}],
        msg="$setUnion should return the single array when 4 of 5 docs are missing",
    ),
]

# Property [$$REMOVE Treated as Missing]: $$REMOVE via $cond is treated as a
# missing field, not as null.
SETUNION_REMOVE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "remove_all",
        docs=[{"v": [1]}, {"v": [2]}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$setUnion": {"$cond": [False, "$v", "$$REMOVE"]}},
                }
            },
        ],
        expected=[{"_id": None, "result": []}],
        msg="$setUnion should treat $$REMOVE as missing and return empty array",
    ),
    AccumulatorTestCase(
        "remove_mixed_with_arrays",
        docs=[{"v": [1, 2], "skip": False}, {"v": [2, 3], "skip": True}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$setUnion": {"$cond": [{"$eq": ["$skip", False]}, "$v", "$$REMOVE"]}
                    },
                }
            },
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2]}],
        msg="$setUnion should skip $$REMOVE documents and union remaining arrays",
    ),
]

# Property [Null as Array Element]: null within an array is a valid element,
# distinct from null as the field value.
SETUNION_NULL_ELEMENT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_element_dedup_across_docs",
        docs=[{"v": [None, 1]}, {"v": [None, 2]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 3}],
        msg="$setUnion should deduplicate null elements across documents",
    ),
    AccumulatorTestCase(
        "null_element_all_null_arrays",
        docs=[{"v": [None]}, {"v": [None]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
        ],
        expected=[{"_id": None, "result": [None]}],
        msg="$setUnion should produce single null when all arrays contain only null",
    ),
    AccumulatorTestCase(
        "null_element_mixed_with_values",
        docs=[{"v": [None, "a"]}, {"v": ["a", "b"]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 3}],
        msg="$setUnion should preserve null element alongside other values",
    ),
]

# Property [Missing Group with Array Group]: when one group has all missing
# and another has arrays, both produce correct independent results.
SETUNION_MISSING_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "missing_group_vs_array_group",
        docs=[
            {"g": "A", "x": 1},
            {"g": "A", "x": 2},
            {"g": "B", "v": [1, 2]},
            {"g": "B", "v": [2, 3]},
        ],
        pipeline=[
            {"$group": {"_id": "$g", "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 1, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": []},
            {"_id": "B", "result": [1, 2, 3]},
        ],
        msg="$setUnion should return [] for all-missing group and union for array group",
    ),
]

# Property [Missing Nested Paths]: when using dotted field paths like $a.b or
# $a.b.c, documents where any segment of the path is missing or is a non-object
# type are silently ignored — only documents where the full path resolves to an
# array contribute to the union.
SETUNION_MISSING_NESTED_PATH_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nested_path_b_missing_in_one_doc",
        docs=[
            {"a": {"b": [1, 2]}},
            {"a": {}},
            {"a": {"b": [2, 3]}},
            {"c": 1},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$a.b"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion on $a.b should ignore docs where a exists but b is missing or a is missing",
    ),
    AccumulatorTestCase(
        "nested_path_a_is_scalar",
        docs=[
            {"a": {"b": [1, 2]}},
            {"a": "scalar"},
            {"a": {"b": [2, 3]}},
            {"a": 42},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$a.b"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion on $a.b should ignore docs where a is a non-object scalar",
    ),
    AccumulatorTestCase(
        "nested_path_three_levels_mixed_missing",
        docs=[
            {"a": {"b": {"c": [1, 2]}}},
            {"a": {"b": {}}},
            {"a": {}},
            {"c": 1},
            {"a": {"b": {"c": [2, 3]}}},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$a.b.c"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion on $a.b.c should ignore docs missing at any level of the path",
    ),
    AccumulatorTestCase(
        "nested_path_a_is_array_traversal_partial_missing",
        docs=[
            {"a": [{"b": [1, 2]}, {"b": [3]}]},
            {"a": [{"b": [3, 4]}, {"c": 5}]},
            {"a": [{"x": 1}]},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$a.b"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [[1, 2], [3], [3, 4]]}],
        msg="$setUnion on $a.b should traverse arrays and skip elements where b is missing",
    ),
    AccumulatorTestCase(
        "nested_path_a_mixed_object_array_bool",
        docs=[
            {"a": {"b": [10, 20]}},
            {"a": [1, 2, 3]},
            {"a": True},
            {"a": {"b": [20, 30]}},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$a.b"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [10, 20, 30]}],
        msg="$setUnion on $a.b should ignore docs where a is array or bool, union objects only",
    ),
]

SETUNION_NULL_MISSING_SUCCESS_TESTS = (
    SETUNION_MISSING_FIELD_TESTS
    + SETUNION_REMOVE_TESTS
    + SETUNION_NULL_ELEMENT_TESTS
    + SETUNION_MISSING_GROUP_TESTS
    + SETUNION_MISSING_NESTED_PATH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_NULL_MISSING_SUCCESS_TESTS))
def test_accumulator_setUnion_null_missing_success(collection, test_case: AccumulatorTestCase):
    """Test $setUnion accumulator null/missing success cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
