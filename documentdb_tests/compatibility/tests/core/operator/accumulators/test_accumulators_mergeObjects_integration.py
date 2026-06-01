"""Tests for $mergeObjects accumulator composed with sibling accumulators in the same $group."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [MergeObjects vs Push]: $mergeObjects shallow-merges per-document
# objects into one result while $push collects them as separate array elements.
MERGEOBJECTS_WITH_PUSH_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mergeObjects_vs_push_disjoint",
        docs=[
            {"_id": 1, "cat": "a", "meta": {"src": "x"}},
            {"_id": 2, "cat": "a", "meta": {"quality": "high"}},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "merged": {"$mergeObjects": "$meta"},
                    "pushed": {"$push": "$meta"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "merged": {"src": "x", "quality": "high"},
                "pushed": [{"src": "x"}, {"quality": "high"}],
            }
        ],
        msg="$mergeObjects should merge into one object while $push collects as array",
    ),
    AccumulatorTestCase(
        "mergeObjects_vs_push_overlap",
        docs=[
            {"_id": 1, "cat": "a", "meta": {"k": 1}},
            {"_id": 2, "cat": "a", "meta": {"k": 2}},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "merged": {"$mergeObjects": "$meta"},
                    "pushed": {"$push": "$meta"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "merged": {"k": 2},
                "pushed": [{"k": 1}, {"k": 2}],
            }
        ],
        msg="$mergeObjects last-wins on overlap while $push preserves both objects",
    ),
]

# Property [MergeObjects vs First/Last]: $mergeObjects combines all documents
# while $first/$last pick one positional value from the sorted group.
MERGEOBJECTS_WITH_FIRST_LAST_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mergeObjects_with_first_last",
        docs=[
            {"_id": 1, "cat": "a", "meta": {"x": 1}, "v": 10},
            {"_id": 2, "cat": "a", "meta": {"y": 2}, "v": 20},
            {"_id": 3, "cat": "a", "meta": {"z": 3}, "v": 30},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "merged": {"$mergeObjects": "$meta"},
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "merged": {"x": 1, "y": 2, "z": 3},
                "first_v": 10,
                "last_v": 30,
            }
        ],
        msg="$mergeObjects should merge all objects while $first/$last pick endpoints",
    ),
]

# Property [MergeObjects vs Sum/Count]: $mergeObjects combines object fields
# while $sum aggregates numeric values and $sum(1) counts documents.
MERGEOBJECTS_WITH_SUM_COUNT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mergeObjects_with_sum_count",
        docs=[
            {"_id": 1, "cat": "a", "meta": {"region": "us"}, "score": 10},
            {"_id": 2, "cat": "a", "meta": {"tier": "gold"}, "score": 20},
            {"_id": 3, "cat": "b", "meta": {"region": "eu"}, "score": 5},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "merged": {"$mergeObjects": "$meta"},
                    "total": {"$sum": "$score"},
                    "count": {"$sum": 1},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "merged": {"region": "us", "tier": "gold"},
                "total": 30,
                "count": 2,
            },
            {"_id": "b", "merged": {"region": "eu"}, "total": 5, "count": 1},
        ],
        msg="$mergeObjects should merge objects while $sum/$count aggregate numbers",
    ),
]

# Property [MergeObjects vs AddToSet]: $mergeObjects merges all objects
# (last-wins on overlap) while $addToSet collects unique scalar values.
MERGEOBJECTS_WITH_ADDTOSET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mergeObjects_vs_addToSet",
        docs=[
            {"_id": 1, "cat": "a", "meta": {"src": "x"}, "tag": "a"},
            {"_id": 2, "cat": "a", "meta": {"src": "y"}, "tag": "b"},
            {"_id": 3, "cat": "a", "meta": {"quality": "high"}, "tag": "a"},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "merged": {"$mergeObjects": "$meta"},
                    "tags": {"$addToSet": "$tag"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "merged": {"src": "y", "quality": "high"},
                "tags": ["a", "b"],
            }
        ],
        msg="$mergeObjects should last-win on 'src' while $addToSet deduplicates tags",
    ),
]

# Property [MergeObjects Null Divergence]: $mergeObjects ignores null while
# sibling accumulators handle null differently -- $push includes it, $sum
# treats it as 0, $first returns it.
MERGEOBJECTS_NULL_DIVERGENCE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mergeObjects_null_vs_push_sum",
        docs=[
            {"_id": 1, "cat": "a", "meta": None, "v": None},
            {"_id": 2, "cat": "a", "meta": {"b": 2}, "v": 10},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "merged": {"$mergeObjects": "$meta"},
                    "pushed": {"$push": "$meta"},
                    "total": {"$sum": "$v"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "merged": {"b": 2},
                "pushed": [None, {"b": 2}],
                "total": 10,
            }
        ],
        msg="$mergeObjects ignores null; $push includes null; $sum treats null as 0",
    ),
    AccumulatorTestCase(
        "mergeObjects_null_vs_first",
        docs=[
            {"_id": 1, "cat": "a", "meta": None, "v": None},
            {"_id": 2, "cat": "a", "meta": {"b": 2}, "v": 10},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "merged": {"$mergeObjects": "$meta"},
                    "first_v": {"$first": "$v"},
                }
            },
        ],
        expected=[
            {"_id": "a", "merged": {"b": 2}, "first_v": None},
        ],
        msg="$mergeObjects ignores null meta; $first returns null as the first value",
    ),
]

# Property [MergeObjects Missing Divergence]: $mergeObjects ignores missing
# fields while $sum ignores them (returns 0) and $push omits them.
MERGEOBJECTS_MISSING_DIVERGENCE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mergeObjects_missing_vs_sum_push",
        docs=[
            {"_id": 1, "cat": "a", "meta": {"x": 1}, "v": 10},
            {"_id": 2, "cat": "a", "v": 20},
            {"_id": 3, "cat": "a", "meta": {"z": 3}},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "merged": {"$mergeObjects": "$meta"},
                    "total": {"$sum": "$v"},
                    "pushed": {"$push": "$meta"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "merged": {"x": 1, "z": 3},
                "total": 30,
                "pushed": [{"x": 1}, {"z": 3}],
            }
        ],
        msg="$mergeObjects skips missing meta; $sum skips missing v; $push omits missing",
    ),
]

# Property [Multiple MergeObjects]: multiple $mergeObjects accumulators in the
# same $group independently merge different fields.
MULTIPLE_MERGEOBJECTS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multiple_mergeObjects_different_fields",
        docs=[
            {"_id": 1, "cat": "a", "meta": {"x": 1}, "cfg": {"debug": True}},
            {"_id": 2, "cat": "a", "meta": {"y": 2}, "cfg": {"verbose": False}},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "merged_meta": {"$mergeObjects": "$meta"},
                    "merged_cfg": {"$mergeObjects": "$cfg"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "merged_meta": {"x": 1, "y": 2},
                "merged_cfg": {"debug": True, "verbose": False},
            }
        ],
        msg="Multiple $mergeObjects accumulators should merge their fields independently",
    ),
]

MERGEOBJECTS_INTEGRATION_TESTS = (
    MERGEOBJECTS_WITH_PUSH_TESTS
    + MERGEOBJECTS_WITH_FIRST_LAST_TESTS
    + MERGEOBJECTS_WITH_SUM_COUNT_TESTS
    + MERGEOBJECTS_WITH_ADDTOSET_TESTS
    + MERGEOBJECTS_NULL_DIVERGENCE_TESTS
    + MERGEOBJECTS_MISSING_DIVERGENCE_TESTS
    + MULTIPLE_MERGEOBJECTS_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MERGEOBJECTS_INTEGRATION_TESTS))
def test_accumulators_mergeObjects_integration(collection, test_case: AccumulatorTestCase):
    """Test $mergeObjects accumulator composed with sibling accumulators in the same $group."""
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
        ignore_order_in=["tags"],
    )
