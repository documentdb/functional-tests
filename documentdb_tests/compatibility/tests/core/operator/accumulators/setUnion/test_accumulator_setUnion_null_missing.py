"""Tests for $setUnion accumulator: null/missing field handling and null elements."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null Field Error]: null field values cause TYPE_MISMATCH_ERROR in
# accumulator context.
SETUNION_NULL_FIELD_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_field_single_doc",
        docs=[{"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject null field value with TYPE_MISMATCH_ERROR",
    ),
    AccumulatorTestCase(
        "null_field_all_docs",
        docs=[{"v": None}, {"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject when all documents have null field",
    ),
    AccumulatorTestCase(
        "null_field_mixed_with_array",
        docs=[{"v": [1, 2]}, {"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject when any document has null field among arrays",
    ),
    AccumulatorTestCase(
        "null_field_before_array",
        docs=[{"v": None}, {"v": [1, 2]}],
        pipeline=[{"$group": {"_id": None, "result": {"$setUnion": "$v"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$setUnion should reject null field regardless of document order",
    ),
]

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
        "missing_three_of_five",
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
        "missing_four_of_five",
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

SETUNION_NULL_MISSING_SUCCESS_TESTS = (
    SETUNION_MISSING_FIELD_TESTS
    + SETUNION_REMOVE_TESTS
    + SETUNION_NULL_ELEMENT_TESTS
    + SETUNION_MISSING_GROUP_TESTS
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


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_NULL_FIELD_ERROR_TESTS))
def test_accumulator_setUnion_null_missing_errors(collection, test_case):
    """Test $setUnion accumulator null field error cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
