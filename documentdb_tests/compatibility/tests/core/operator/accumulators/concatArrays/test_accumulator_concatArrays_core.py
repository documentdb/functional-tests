"""Tests for $concatArrays accumulator: core concatenation behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Core Concatenation]: $concatArrays concatenates arrays from
# multiple documents in order, preserving all elements.
CONCATARRAYS_CORE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "core_concat_multiple_arrays",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": [3, 4]},
            {"_id": 3, "v": [5]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, 2, 3, 4, 5]}],
        msg="$concatArrays should concatenate arrays from multiple documents in order",
    ),
    AccumulatorTestCase(
        "core_single_array_passthrough",
        docs=[{"_id": 1, "v": [1, 2, 3]}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        expected=[{"_id": None, "result": [1, 2, 3]}],
        msg="$concatArrays should return the array unchanged for a single document",
    ),
    AccumulatorTestCase(
        "core_preserves_order",
        docs=[
            {"_id": 1, "v": [3, 1]},
            {"_id": 2, "v": [2, 4]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [3, 1, 2, 4]}],
        msg="$concatArrays should preserve element order within and across documents",
    ),
    AccumulatorTestCase(
        "core_many_docs_unique",
        docs=[{"_id": i, "v": [i]} for i in range(100)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": list(range(100))}],
        msg="$concatArrays should concatenate 100 single-element arrays in order",
    ),
    AccumulatorTestCase(
        "core_many_docs_repeated_values",
        docs=[{"_id": i, "v": [i % 5]} for i in range(100)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [i % 5 for i in range(100)]}],
        msg="$concatArrays should preserve all 100 elements even with repeated values",
    ),
]

# Property [Duplicate Preservation]: $concatArrays preserves all elements
# including duplicates, unlike $addToSet.
CONCATARRAYS_DUPLICATE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "dup_overlapping_elements",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": [2, 3]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, 2, 2, 3]}],
        msg="$concatArrays should preserve duplicate elements across documents",
    ),
    AccumulatorTestCase(
        "dup_within_and_across",
        docs=[
            {"_id": 1, "v": [1, 1]},
            {"_id": 2, "v": [1, 1]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, 1, 1, 1]}],
        msg="$concatArrays should preserve all duplicates within and across documents",
    ),
    AccumulatorTestCase(
        "dup_identical_arrays",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": [1, 2]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, 2, 1, 2]}],
        msg="$concatArrays should concatenate identical arrays without deduplication",
    ),
    AccumulatorTestCase(
        "dup_string_duplicates",
        docs=[
            {"_id": 1, "v": ["a", "a"]},
            {"_id": 2, "v": ["a", "b"]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": ["a", "a", "a", "b"]}],
        msg="$concatArrays should preserve string duplicates across documents",
    ),
]

# Property [Empty Array Handling]: empty arrays contribute nothing to the
# result but do not cause errors.
CONCATARRAYS_EMPTY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "empty_all_empty_arrays",
        docs=[{"_id": 1, "v": []}, {"_id": 2, "v": []}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        expected=[{"_id": None, "result": []}],
        msg="$concatArrays should return empty array when all inputs are empty arrays",
    ),
    AccumulatorTestCase(
        "empty_single_empty_array",
        docs=[{"_id": 1, "v": []}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        expected=[{"_id": None, "result": []}],
        msg="$concatArrays should return empty array for a single empty array input",
    ),
    AccumulatorTestCase(
        "empty_mixed_with_nonempty",
        docs=[
            {"_id": 1, "v": []},
            {"_id": 2, "v": [1, 2]},
            {"_id": 3, "v": []},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, 2]}],
        msg="$concatArrays should skip empty arrays and concatenate non-empty ones",
    ),
    AccumulatorTestCase(
        "empty_before_nonempty",
        docs=[
            {"_id": 1, "v": []},
            {"_id": 2, "v": [3, 4]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [3, 4]}],
        msg="$concatArrays should handle empty array before non-empty array",
    ),
    AccumulatorTestCase(
        "empty_after_nonempty",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": []},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, 2]}],
        msg="$concatArrays should handle empty array after non-empty array",
    ),
]

# Property [Nested Array Behavior]: $concatArrays treats nested arrays as
# atomic elements without unwinding them.
CONCATARRAYS_NESTED_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nested_arrays_as_elements",
        docs=[
            {"_id": 1, "v": [[1, 2]]},
            {"_id": 2, "v": [[3, 4]]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [[1, 2], [3, 4]]}],
        msg="$concatArrays should treat nested arrays as atomic elements",
    ),
    AccumulatorTestCase(
        "nested_mixed_depth",
        docs=[
            {"_id": 1, "v": [1, [2]]},
            {"_id": 2, "v": [[3], 4]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, [2], [3], 4]}],
        msg="$concatArrays should preserve mixed-depth nesting",
    ),
    AccumulatorTestCase(
        "nested_deeply",
        docs=[
            {"_id": 1, "v": [[[1]]]},
            {"_id": 2, "v": [[[2]]]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [[[1]], [[2]]]}],
        msg="$concatArrays should preserve deeply nested arrays as atomic elements",
    ),
]

# Property [Grouping Independence]: multiple groups compute $concatArrays
# independently.
CONCATARRAYS_GROUPING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "grouping_two_groups",
        docs=[
            {"_id": 1, "g": "A", "v": [1, 2]},
            {"_id": 2, "g": "A", "v": [3]},
            {"_id": 3, "g": "B", "v": [10]},
            {"_id": 4, "g": "B", "v": [20]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": "$g", "result": {"$concatArrays": "$v"}}},
        ],
        expected=[
            {"_id": "A", "result": [1, 2, 3]},
            {"_id": "B", "result": [10, 20]},
        ],
        msg="$concatArrays should compute independently per group",
    ),
    AccumulatorTestCase(
        "grouping_three_groups",
        docs=[
            {"_id": 1, "g": "X", "v": [1]},
            {"_id": 2, "g": "Y", "v": [2]},
            {"_id": 3, "g": "Z", "v": [3]},
            {"_id": 4, "g": "X", "v": [4]},
            {"_id": 5, "g": "Y", "v": [5]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": "$g", "result": {"$concatArrays": "$v"}}},
        ],
        expected=[
            {"_id": "X", "result": [1, 4]},
            {"_id": "Y", "result": [2, 5]},
            {"_id": "Z", "result": [3]},
        ],
        msg="$concatArrays should compute independently across three groups",
    ),
]

# Property [Return Type]: $concatArrays always returns an array type regardless
# of input element types.
CONCATARRAYS_RETURN_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "return_type_numeric_arrays",
        docs=[{"v": [1, 2]}, {"v": [3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "array"}],
        msg="$concatArrays should return array type for numeric element arrays",
    ),
    AccumulatorTestCase(
        "return_type_string_arrays",
        docs=[{"v": ["a"]}, {"v": ["b"]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "array"}],
        msg="$concatArrays should return array type for string element arrays",
    ),
    AccumulatorTestCase(
        "return_type_empty_arrays",
        docs=[{"v": []}, {"v": []}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "array"}],
        msg="$concatArrays should return array type for empty array inputs",
    ),
    AccumulatorTestCase(
        "return_type_all_missing",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
            {"$project": {"_id": 0, "type": {"$type": "$result"}}},
        ],
        expected=[{"type": "array"}],
        msg="$concatArrays should return array type even when all inputs are missing",
    ),
]

# Property [Empty Collection]: empty collection produces no group output.
CONCATARRAYS_EMPTY_COLLECTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "empty_collection",
        docs=None,
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        expected=[],
        msg="$concatArrays on empty collection should return empty result set",
    ),
]

CONCATARRAYS_ALL_CORE_TESTS = (
    CONCATARRAYS_CORE_TESTS
    + CONCATARRAYS_DUPLICATE_TESTS
    + CONCATARRAYS_EMPTY_TESTS
    + CONCATARRAYS_NESTED_TESTS
    + CONCATARRAYS_GROUPING_TESTS
    + CONCATARRAYS_RETURN_TYPE_TESTS
    + CONCATARRAYS_EMPTY_COLLECTION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONCATARRAYS_ALL_CORE_TESTS))
def test_accumulator_concatArrays_core(collection, test_case: AccumulatorTestCase):
    """Test $concatArrays core concatenation, grouping, return type, and empty collection."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)
