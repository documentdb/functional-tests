"""Tests for $first accumulator composed with sibling accumulators in the same $group."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [First with Last]: $first and $last coexist in the same $group,
# picking the first and last values respectively.  A preceding $sort
# establishes deterministic order.
FIRST_WITH_LAST_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "first_last_sorted_asc",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "first_v": 10, "last_v": 30}],
        msg="$first should pick smallest and $last should pick largest after ascending sort",
    ),
    AccumulatorTestCase(
        "first_last_sorted_desc",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {"$sort": {"v": -1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "first_v": 30, "last_v": 10}],
        msg="$first should pick largest and $last should pick smallest after descending sort",
    ),
    AccumulatorTestCase(
        "first_last_multiple_groups",
        docs=[
            {"cat": "a", "v": 5},
            {"cat": "a", "v": 15},
            {"cat": "b", "v": 100},
            {"cat": "b", "v": 200},
            {"cat": "b", "v": 300},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[
            {"_id": "a", "first_v": 5, "last_v": 15},
            {"_id": "b", "first_v": 100, "last_v": 300},
        ],
        msg="$first and $last should work independently across multiple groups",
    ),
    AccumulatorTestCase(
        "first_last_null_first_doc",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "first_v": None, "last_v": 20}],
        msg="$first should return null (null sorts first) while $last returns 20",
    ),
]

# Property [First with Min/Max]: $first is position-based while $min/$max
# are value-based.  The same data can produce different $first results
# depending on sort order, but $min/$max are always the same.
FIRST_WITH_MIN_MAX_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "first_min_max_sorted_asc",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "first_v": 10, "lo": 10, "hi": 30}],
        msg="$first equals $min after ascending sort; $max is independent",
    ),
    AccumulatorTestCase(
        "first_min_max_sorted_desc",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {"$sort": {"v": -1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "first_v": 30, "lo": 10, "hi": 30}],
        msg="$first equals $max after descending sort; $min/$max unchanged",
    ),
    AccumulatorTestCase(
        "first_min_max_null_divergence",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 5},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "first_v": None, "lo": 5, "hi": 10}],
        msg="$first returns null (includes it) while $min/$max ignore null",
    ),
]

# Property [First with Sum/Avg]: $first picks one value, $sum/$avg
# aggregate all.  Null divergence: $first returns null when it's in the
# first position; $sum treats null as 0; $avg excludes null from count.
FIRST_WITH_SUM_AVG_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "first_sum_avg_basic",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 30},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "total": {"$sum": "$v"},
                    "mean": {"$avg": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "first_v": 10, "total": 60, "mean": 20.0}],
        msg="$first picks 10 while $sum and $avg compute over all values",
    ),
    AccumulatorTestCase(
        "first_sum_avg_null_first_doc",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "total": {"$sum": "$v"},
                    "mean": {"$avg": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "first_v": None, "total": 30, "mean": 15.0}],
        msg="$first returns null; $sum ignores null (30); $avg ignores null (15.0)",
    ),
    AccumulatorTestCase(
        "first_sum_avg_all_null",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "total": {"$sum": "$v"},
                    "mean": {"$avg": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "first_v": None, "total": 0, "mean": None}],
        msg="$first returns null; $sum returns 0; $avg returns null when all null",
    ),
]

# Property [First with Count]: $first picks one value while $count counts
# all documents in the group.
FIRST_WITH_COUNT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "first_count_basic",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "b", "v": 5},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "n": {"$sum": 1},
                }
            },
        ],
        expected=[
            {"_id": "a", "first_v": 10, "n": 2},
            {"_id": "b", "first_v": 5, "n": 1},
        ],
        msg="$first picks one value while $sum(1) counts all docs per group",
    ),
    AccumulatorTestCase(
        "first_count_null_counted",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "n": {"$sum": 1},
                }
            },
        ],
        expected=[{"_id": "a", "first_v": None, "n": 2}],
        msg="$first returns null; $sum(1) still counts the null doc",
    ),
]

# Property [First with Push/AddToSet]: $first picks one value while $push
# collects all values and $addToSet collects unique values.
FIRST_WITH_PUSH_ADDTOSET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "first_push_addtoset",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 10},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "all_vals": {"$push": "$v"},
                    "unique_vals": {"$addToSet": "$v"},
                }
            },
        ],
        expected=[
            {"_id": "a", "first_v": 10, "all_vals": [10, 10, 20], "unique_vals": [10, 20]},
        ],
        msg="$first picks 10 while $push collects all and $addToSet collects unique",
    ),
    AccumulatorTestCase(
        "first_push_null_handling",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "all_vals": {"$push": "$v"},
                }
            },
        ],
        expected=[
            {"_id": "a", "first_v": None, "all_vals": [None, 10]},
        ],
        msg="$first returns null; $push includes null in the collected array",
    ),
]

# Property [First with MergeObjects]: $first picks one scalar value while
# $mergeObjects combines per-document subdocuments into one merged object.
FIRST_WITH_MERGE_OBJECTS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "first_merge_objects",
        docs=[
            {"cat": "a", "v": 10, "meta": {"src": "x"}},
            {"cat": "a", "v": 20, "meta": {"quality": "high"}},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "merged": {"$mergeObjects": "$meta"},
                }
            },
        ],
        expected=[
            {"_id": "a", "first_v": 10, "merged": {"src": "x", "quality": "high"}},
        ],
        msg="$first picks 10 while $mergeObjects combines all metadata objects",
    ),
]

# Property [Multiple First]: multiple $first accumulators in the same $group
# independently pick the first value from different fields.
MULTIPLE_FIRST_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multiple_first_different_fields",
        docs=[
            {"cat": "a", "name": "alice", "score": 85},
            {"cat": "a", "name": "bob", "score": 92},
            {"cat": "b", "name": "carol", "score": 78},
        ],
        pipeline=[
            {"$sort": {"score": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_name": {"$first": "$name"},
                    "first_score": {"$first": "$score"},
                }
            },
        ],
        expected=[
            {"_id": "a", "first_name": "alice", "first_score": 85},
            {"_id": "b", "first_name": "carol", "first_score": 78},
        ],
        msg="Multiple $first accumulators should independently pick first from each field",
    ),
    AccumulatorTestCase(
        "multiple_first_one_missing",
        docs=[
            {"cat": "a", "score": 85},
            {"cat": "a", "name": "bob", "score": 92},
        ],
        pipeline=[
            {"$sort": {"score": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_name": {"$first": "$name"},
                    "first_score": {"$first": "$score"},
                }
            },
        ],
        expected=[{"_id": "a", "first_name": None, "first_score": 85}],
        msg="$first returns null for missing field while sibling $first returns value",
    ),
]

# Property [First Type Preservation with Sibling]: $first preserves the BSON
# type of the first document's value, even when sibling accumulators promote
# types (e.g. $sum promoting int32+Decimal128 to Decimal128).
FIRST_TYPE_PRESERVATION_WITH_SIBLING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "first_int32_with_sum_decimal128",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": Decimal128("20.5")},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "total": {"$sum": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "first_v": 10, "total": Decimal128("30.5")}],
        msg="$first preserves int32 while $sum promotes to Decimal128",
    ),
    AccumulatorTestCase(
        "first_int64_with_sum_double",
        docs=[
            {"cat": "a", "v": Int64(100)},
            {"cat": "a", "v": 2.5},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "first_v": {"$first": "$v"},
                    "total": {"$sum": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "first_v": 2.5, "total": 102.5}],
        msg="$first preserves double (2.5 sorts first) while $sum promotes to double",
    ),
]

FIRST_INTEGRATION_TESTS = (
    FIRST_WITH_LAST_TESTS
    + FIRST_WITH_MIN_MAX_TESTS
    + FIRST_WITH_SUM_AVG_TESTS
    + FIRST_WITH_COUNT_TESTS
    + FIRST_WITH_PUSH_ADDTOSET_TESTS
    + FIRST_WITH_MERGE_OBJECTS_TESTS
    + MULTIPLE_FIRST_TESTS
    + FIRST_TYPE_PRESERVATION_WITH_SIBLING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(FIRST_INTEGRATION_TESTS))
def test_accumulators_first_integration(collection, test_case: AccumulatorTestCase):
    """Test $first accumulator composed with sibling accumulators in the same $group."""
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
        ignore_order_in=["unique_vals"],
    )
