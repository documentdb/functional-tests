"""Tests for $setUnion accumulator: core accumulation, grouping, and identity behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Core Accumulation]: $setUnion unions arrays from multiple documents
# within a group, producing one array containing all unique elements.
SETUNION_CORE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "core_disjoint_two_docs",
        docs=[{"v": [1, 2]}, {"v": [3, 4]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3, 4]}],
        msg="$setUnion should union disjoint arrays from two documents",
    ),
    AccumulatorTestCase(
        "core_overlapping_three_docs",
        docs=[{"v": [1, 2]}, {"v": [2, 3]}, {"v": [3, 4]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3, 4]}],
        msg="$setUnion should deduplicate overlapping elements across three documents",
    ),
    AccumulatorTestCase(
        "core_all_identical_five_docs",
        docs=[{"v": [1, 2, 3]} for _ in range(5)],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should deduplicate when all five documents have the same array",
    ),
    AccumulatorTestCase(
        "core_single_doc",
        docs=[{"v": [1, 2, 3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should return the document's array when there is a single document",
    ),
    AccumulatorTestCase(
        "core_single_doc_intra_dedup",
        docs=[{"v": [1, 1, 2, 2, 3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should deduplicate within a single document's array",
    ),
    AccumulatorTestCase(
        "core_shared_element_all_docs",
        docs=[{"v": [1, 10]}, {"v": [1, 20]}, {"v": [1, 30]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 10, 20, 30]}],
        msg="$setUnion should keep shared element once and preserve unique elements",
    ),
    AccumulatorTestCase(
        "core_large_overlap_ten_docs",
        docs=[{"v": [1, 2, 3, 4, 5]} for _ in range(10)],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3, 4, 5]}],
        msg="$setUnion should deduplicate across 10 documents with identical arrays",
    ),
]

# Property [Empty Array Identity]: empty arrays act as the identity element
# for set union.
SETUNION_EMPTY_ARRAY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "empty_all_docs",
        docs=[{"v": []}, {"v": []}, {"v": []}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
        ],
        expected=[{"_id": None, "result": []}],
        msg="$setUnion should return empty array when all documents have empty arrays",
    ),
    AccumulatorTestCase(
        "empty_mixed_with_values",
        docs=[{"v": []}, {"v": [1, 2]}, {"v": []}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2]}],
        msg="$setUnion should ignore empty arrays and return values from non-empty docs",
    ),
    AccumulatorTestCase(
        "empty_identity_element",
        docs=[{"v": []}, {"v": [3, 4]}, {"v": [4, 5]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [3, 4, 5]}],
        msg="$setUnion should treat empty array as identity in union with non-empty arrays",
    ),
]

# Property [Nested Arrays as Opaque Elements]: nested arrays are treated as
# opaque top-level elements, not flattened or descended into.
SETUNION_NESTED_ARRAY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nested_disjoint",
        docs=[{"v": [[1, 2]]}, {"v": [[3, 4]]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [[1, 2], [3, 4]]}],
        msg="$setUnion should treat nested arrays as opaque elements without flattening",
    ),
    AccumulatorTestCase(
        "nested_identical_dedup",
        docs=[{"v": [[1, 2]]}, {"v": [[1, 2]]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
        ],
        expected=[{"_id": None, "result": [[1, 2]]}],
        msg="$setUnion should deduplicate identical nested arrays",
    ),
    AccumulatorTestCase(
        "nested_order_matters",
        docs=[{"v": [[1, 2]]}, {"v": [[2, 1]]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 2}],
        msg="$setUnion should treat [1,2] and [2,1] as distinct nested array elements",
    ),
]

# Property [Multiple Groups]: $setUnion operates independently per group with
# no state leaking between groups.
SETUNION_MULTIPLE_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "groups_two_independent",
        docs=[
            {"g": "A", "v": [1, 2]},
            {"g": "A", "v": [2, 3]},
            {"g": "B", "v": [10, 20]},
            {"g": "B", "v": [20, 30]},
        ],
        pipeline=[
            {"$group": {"_id": "$g", "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 1, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": [1, 2, 3]},
            {"_id": "B", "result": [10, 20, 30]},
        ],
        msg="$setUnion should produce independent results for each group",
    ),
    AccumulatorTestCase(
        "groups_three_different_sizes",
        docs=[
            {"g": "X", "v": [1]},
            {"g": "Y", "v": [2]},
            {"g": "Y", "v": [3]},
            {"g": "Z", "v": [4]},
            {"g": "Z", "v": [5]},
            {"g": "Z", "v": [6]},
        ],
        pipeline=[
            {"$group": {"_id": "$g", "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 1, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "X", "result": [1]},
            {"_id": "Y", "result": [2, 3]},
            {"_id": "Z", "result": [4, 5, 6]},
        ],
        msg="$setUnion should handle groups of different sizes independently",
    ),
    AccumulatorTestCase(
        "groups_no_state_leak",
        docs=[
            {"g": "A", "v": [1, 2, 3]},
            {"g": "B", "v": [4, 5, 6]},
        ],
        pipeline=[
            {"$group": {"_id": "$g", "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 1, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": [1, 2, 3]},
            {"_id": "B", "result": [4, 5, 6]},
        ],
        msg="$setUnion should not leak state between groups",
    ),
    AccumulatorTestCase(
        "groups_overlapping_values_different_keys",
        docs=[
            {"g": "A", "v": [1, 2]},
            {"g": "B", "v": [1, 2]},
            {"g": "A", "v": [3]},
            {"g": "B", "v": [3]},
        ],
        pipeline=[
            {"$group": {"_id": "$g", "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 1, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": [1, 2, 3]},
            {"_id": "B", "result": [1, 2, 3]},
        ],
        msg="$setUnion should produce independent results even with overlapping element values",
    ),
]

# Property [Grouping Key Variations]: $setUnion works with different _id
# grouping expressions.
SETUNION_GROUPING_KEY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "grouping_null_id",
        docs=[{"v": [1, 2]}, {"v": [2, 3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should work with _id: null grouping all documents",
    ),
    AccumulatorTestCase(
        "grouping_field_value",
        docs=[
            {"cat": "A", "v": [1]},
            {"cat": "A", "v": [2]},
            {"cat": "B", "v": [3]},
        ],
        pipeline=[
            {"$group": {"_id": "$cat", "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 1, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": [1, 2]},
            {"_id": "B", "result": [3]},
        ],
        msg="$setUnion should work with _id grouping by field value",
    ),
    AccumulatorTestCase(
        "grouping_compound_key",
        docs=[
            {"cat": "A", "sub": "x", "v": [1]},
            {"cat": "A", "sub": "x", "v": [2]},
            {"cat": "A", "sub": "y", "v": [3]},
        ],
        pipeline=[
            {"$group": {"_id": {"cat": "$cat", "sub": "$sub"}, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 1, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
            {"$sort": {"_id.sub": 1}},
        ],
        expected=[
            {"_id": {"cat": "A", "sub": "x"}, "result": [1, 2]},
            {"_id": {"cat": "A", "sub": "y"}, "result": [3]},
        ],
        msg="$setUnion should work with compound _id grouping key",
    ),
]

# Property [Large Groups]: $setUnion correctly accumulates across many
# documents.
SETUNION_LARGE_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "large_100_unique_elements",
        docs=[{"v": [i]} for i in range(100)],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 100}],
        msg="$setUnion should produce 100 elements from 100 documents with unique values",
    ),
    AccumulatorTestCase(
        "large_100_same_element",
        docs=[{"v": [42]} for _ in range(100)],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
        ],
        expected=[{"_id": None, "result": [42]}],
        msg="$setUnion should produce 1 element from 100 documents with the same value",
    ),
    AccumulatorTestCase(
        "large_arrays_100_elements_each",
        docs=[
            {"v": list(range(100))},
            {"v": list(range(50, 150))},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "size": {"$size": "$result"}}},
        ],
        expected=[{"size": 150}],
        msg="$setUnion should correctly union large arrays with overlap",
    ),
]

SETUNION_CORE_SUCCESS_TESTS = (
    SETUNION_CORE_TESTS
    + SETUNION_EMPTY_ARRAY_TESTS
    + SETUNION_NESTED_ARRAY_TESTS
    + SETUNION_MULTIPLE_GROUP_TESTS
    + SETUNION_GROUPING_KEY_TESTS
    + SETUNION_LARGE_GROUP_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_CORE_SUCCESS_TESTS))
def test_accumulator_setUnion_core(collection, test_case: AccumulatorTestCase):
    """Test $setUnion accumulator core behavior."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
