"""Tests for $setUnion accumulator composed with sibling accumulators in the same $group."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [SetUnion with Sum]: $setUnion collects unique array elements while
# $sum independently computes a total from a numeric field.
SETUNION_WITH_SUM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "setunion_sum_single_group",
        docs=[
            {"cat": "a", "tags": [1, 2], "v": 10},
            {"cat": "a", "tags": [2, 3], "v": 20},
            {"cat": "a", "tags": [3, 4], "v": 30},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "all_tags": {"$setUnion": "$tags"},
                    "total": {"$sum": "$v"},
                }
            },
            {
                "$project": {
                    "all_tags": {"$sortArray": {"input": "$all_tags", "sortBy": 1}},
                    "total": 1,
                }
            },
        ],
        expected=[{"_id": "a", "all_tags": [1, 2, 3, 4], "total": 60}],
        msg="$setUnion and $sum should independently compute unique tags and total",
    ),
    AccumulatorTestCase(
        "setunion_sum_multiple_groups",
        docs=[
            {"cat": "a", "tags": [1, 2], "v": 10},
            {"cat": "a", "tags": [2, 3], "v": 20},
            {"cat": "b", "tags": [5, 6], "v": 5},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "all_tags": {"$setUnion": "$tags"},
                    "total": {"$sum": "$v"},
                }
            },
            {
                "$project": {
                    "all_tags": {"$sortArray": {"input": "$all_tags", "sortBy": 1}},
                    "total": 1,
                }
            },
        ],
        expected=[
            {"_id": "a", "all_tags": [1, 2, 3], "total": 30},
            {"_id": "b", "all_tags": [5, 6], "total": 5},
        ],
        msg="$setUnion and $sum should produce correct results across multiple groups",
    ),
]

# Property [SetUnion with AddToSet]: $setUnion merges per-document arrays into
# a flat unique set while $addToSet collects distinct per-document values.
SETUNION_WITH_ADDTOSET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "setunion_addtoset_basic",
        docs=[
            {"cat": "a", "tags": [1, 2], "status": "open"},
            {"cat": "a", "tags": [2, 3], "status": "closed"},
            {"cat": "a", "tags": [3, 4], "status": "open"},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "all_tags": {"$setUnion": "$tags"},
                    "statuses": {"$addToSet": "$status"},
                }
            },
            {
                "$project": {
                    "all_tags": {"$sortArray": {"input": "$all_tags", "sortBy": 1}},
                    "statuses": {"$sortArray": {"input": "$statuses", "sortBy": 1}},
                }
            },
        ],
        expected=[
            {"_id": "a", "all_tags": [1, 2, 3, 4], "statuses": ["closed", "open"]},
        ],
        msg="$setUnion merges arrays while $addToSet collects distinct scalar values",
    ),
]

# Property [SetUnion with Push]: $setUnion deduplicates across arrays while
# $push collects every value (including duplicates).
SETUNION_WITH_PUSH_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "setunion_push_basic",
        docs=[
            {"cat": "a", "tags": [1, 2], "v": 10},
            {"cat": "a", "tags": [2, 3], "v": 10},
            {"cat": "a", "tags": [3, 4], "v": 20},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "all_tags": {"$setUnion": "$tags"},
                    "all_vals": {"$push": "$v"},
                }
            },
            {
                "$project": {
                    "all_tags": {"$sortArray": {"input": "$all_tags", "sortBy": 1}},
                    "all_vals": 1,
                }
            },
        ],
        expected=[
            {"_id": "a", "all_tags": [1, 2, 3, 4], "all_vals": [10, 10, 20]},
        ],
        msg="$setUnion deduplicates while $push keeps all values including duplicates",
    ),
]

# Property [SetUnion with Count]: $setUnion collects unique elements while
# $sum(1) counts all documents in the group.
SETUNION_WITH_COUNT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "setunion_count_basic",
        docs=[
            {"cat": "a", "tags": [1, 2]},
            {"cat": "a", "tags": [2, 3]},
            {"cat": "b", "tags": [10]},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "all_tags": {"$setUnion": "$tags"},
                    "count": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "all_tags": {"$sortArray": {"input": "$all_tags", "sortBy": 1}},
                    "count": 1,
                }
            },
        ],
        expected=[
            {"_id": "a", "all_tags": [1, 2, 3], "count": 2},
            {"_id": "b", "all_tags": [10], "count": 1},
        ],
        msg="$setUnion collects unique tags while $sum(1) counts documents",
    ),
]

# Property [SetUnion with Min/Max]: $setUnion collects unique elements while
# $min and $max independently pick the minimum and maximum scalar values.
SETUNION_WITH_MIN_MAX_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "setunion_min_max_basic",
        docs=[
            {"cat": "a", "tags": [1, 2], "v": 30},
            {"cat": "a", "tags": [2, 3], "v": 10},
            {"cat": "a", "tags": [3, 4], "v": 20},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "all_tags": {"$setUnion": "$tags"},
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            },
            {
                "$project": {
                    "all_tags": {"$sortArray": {"input": "$all_tags", "sortBy": 1}},
                    "lo": 1,
                    "hi": 1,
                }
            },
        ],
        expected=[{"_id": "a", "all_tags": [1, 2, 3, 4], "lo": 10, "hi": 30}],
        msg="$setUnion collects unique tags while $min/$max pick extremes",
    ),
]

# Property [SetUnion with First/Last]: $setUnion is order-independent while
# $first/$last pick positional values.  A preceding $sort establishes order
# for $first and $last.
SETUNION_WITH_FIRST_LAST_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "setunion_first_last_with_sort",
        docs=[
            {"cat": "a", "tags": [1, 2], "v": 30},
            {"cat": "a", "tags": [2, 3], "v": 10},
            {"cat": "a", "tags": [3, 4], "v": 20},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "all_tags": {"$setUnion": "$tags"},
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
            {
                "$project": {
                    "all_tags": {"$sortArray": {"input": "$all_tags", "sortBy": 1}},
                    "first_v": 1,
                    "last_v": 1,
                }
            },
        ],
        expected=[{"_id": "a", "all_tags": [1, 2, 3, 4], "first_v": 10, "last_v": 30}],
        msg="$setUnion should compute union while $first/$last pick sorted extremes",
    ),
]

# Property [SetUnion with MergeObjects]: $setUnion collects unique elements
# while $mergeObjects combines per-document metadata into a single object.
SETUNION_WITH_MERGE_OBJECTS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "setunion_merge_objects",
        docs=[
            {"cat": "a", "tags": [1, 2], "meta": {"src": "x"}},
            {"cat": "a", "tags": [2, 3], "meta": {"quality": "high"}},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "all_tags": {"$setUnion": "$tags"},
                    "merged": {"$mergeObjects": "$meta"},
                }
            },
            {
                "$project": {
                    "all_tags": {"$sortArray": {"input": "$all_tags", "sortBy": 1}},
                    "merged": 1,
                }
            },
        ],
        expected=[
            {"_id": "a", "all_tags": [1, 2, 3], "merged": {"src": "x", "quality": "high"}},
        ],
        msg="$setUnion collects unique tags while $mergeObjects combines metadata",
    ),
]

# Property [Multiple SetUnion Expressions]: multiple $setUnion accumulators in
# the same $group independently merge different array fields.
MULTIPLE_SETUNION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multiple_setunion_different_fields",
        docs=[
            {"cat": "a", "tags": [1, 2], "colors": ["red", "blue"]},
            {"cat": "a", "tags": [2, 3], "colors": ["blue", "green"]},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "all_tags": {"$setUnion": "$tags"},
                    "all_colors": {"$setUnion": "$colors"},
                }
            },
            {
                "$project": {
                    "all_tags": {"$sortArray": {"input": "$all_tags", "sortBy": 1}},
                    "all_colors": {"$sortArray": {"input": "$all_colors", "sortBy": 1}},
                }
            },
        ],
        expected=[
            {"_id": "a", "all_tags": [1, 2, 3], "all_colors": ["blue", "green", "red"]},
        ],
        msg="Multiple $setUnion accumulators should independently merge different array fields",
    ),
    AccumulatorTestCase(
        "multiple_setunion_multiple_groups",
        docs=[
            {"cat": "a", "tags": [1, 2], "ids": ["x"]},
            {"cat": "a", "tags": [2, 3], "ids": ["x", "y"]},
            {"cat": "b", "tags": [10], "ids": ["z"]},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "all_tags": {"$setUnion": "$tags"},
                    "all_ids": {"$setUnion": "$ids"},
                }
            },
            {
                "$project": {
                    "all_tags": {"$sortArray": {"input": "$all_tags", "sortBy": 1}},
                    "all_ids": {"$sortArray": {"input": "$all_ids", "sortBy": 1}},
                }
            },
        ],
        expected=[
            {"_id": "a", "all_tags": [1, 2, 3], "all_ids": ["x", "y"]},
            {"_id": "b", "all_tags": [10], "all_ids": ["z"]},
        ],
        msg="Multiple $setUnion accumulators should work across multiple groups",
    ),
]

# Property [SetUnion Missing-Field Handling with Sibling]: $setUnion skips
# missing fields while sibling accumulators handle them per their own rules.
SETUNION_MISSING_WITH_SIBLING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "setunion_missing_with_sum",
        docs=[
            {"cat": "a", "tags": [1, 2], "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "tags": [2, 3], "v": 30},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "all_tags": {"$setUnion": "$tags"},
                    "total": {"$sum": "$v"},
                }
            },
            {
                "$project": {
                    "all_tags": {"$sortArray": {"input": "$all_tags", "sortBy": 1}},
                    "total": 1,
                }
            },
        ],
        expected=[{"_id": "a", "all_tags": [1, 2, 3], "total": 60}],
        msg="$setUnion skips missing fields while $sum independently totals all numeric values",
    ),
]

SETUNION_INTEGRATION_TESTS = (
    SETUNION_WITH_SUM_TESTS
    + SETUNION_WITH_ADDTOSET_TESTS
    + SETUNION_WITH_PUSH_TESTS
    + SETUNION_WITH_COUNT_TESTS
    + SETUNION_WITH_MIN_MAX_TESTS
    + SETUNION_WITH_FIRST_LAST_TESTS
    + SETUNION_WITH_MERGE_OBJECTS_TESTS
    + MULTIPLE_SETUNION_TESTS
    + SETUNION_MISSING_WITH_SIBLING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_INTEGRATION_TESTS))
def test_accumulators_setUnion_integration(collection, test_case: AccumulatorTestCase):
    """Test $setUnion accumulator composed with sibling accumulators in the same $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )
