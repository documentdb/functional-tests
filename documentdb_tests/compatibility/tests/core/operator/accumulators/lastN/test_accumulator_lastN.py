"""Tests for $lastN accumulator: n-vs-size behavior, per-group accumulation, sort
order, null/missing, mixed types, and empty-group handling.

$lastN returns the last ``n`` elements of a group as an array, ordered by the
preceding $sort stage.

Not covered by design: pipelines with no $sort, and tied sort keys -- which
documents land in the last n is unspecified, so any assertion would be flaky."""

from __future__ import annotations

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [n vs Group Size]: $lastN returns min(n, group size) elements, and
# n == 1 returns a single-element list rather than a scalar.
LASTN_N_VALUE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "n_greater_than_size",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": 20}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 5, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, 20]}],
        msg="$lastN should return all available values when n exceeds group size",
    ),
    AccumulatorTestCase(
        "n_equal_to_size",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": 20}, {"_id": 2, "v": 30}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 3, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [10, 20, 30]}],
        msg="$lastN should return all values when n equals group size",
    ),
    AccumulatorTestCase(
        "n_less_than_size",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": 20}, {"_id": 2, "v": 30}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 2, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [20, 30]}],
        msg="$lastN should return only the last n values when n is less than group size",
    ),
    AccumulatorTestCase(
        "n_equals_one",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": 20}, {"_id": 2, "v": 30}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 1, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [30]}],
        msg="$lastN with n=1 should return a single-element list, not a scalar",
    ),
    AccumulatorTestCase(
        "n_as_long",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": 20}, {"_id": 2, "v": 30}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$lastN": {"n": {"$toLong": 2}, "input": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [20, 30]}],
        msg="$lastN should accept a long-typed n value",
    ),
]

# Property [Per-Group Accumulation]: each group accumulates independently and n
# applies per group, so a group with fewer than n documents yields only what it has.
LASTN_MULTIPLE_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "groups_two_independent",
        docs=[
            {"_id": 0, "cat": "A", "v": 10},
            {"_id": 1, "cat": "A", "v": 20},
            {"_id": 2, "cat": "A", "v": 30},
            {"_id": 3, "cat": "B", "v": 40},
        ],
        # No $project: _id carries the group identity under test. The trailing
        # $sort makes document order deterministic.
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": "$cat", "result": {"$lastN": {"n": 2, "input": "$v"}}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": "A", "result": [20, 30]}, {"_id": "B", "result": [40]}],
        msg="$lastN should accumulate independently per group",
    ),
]

# Property [Sort Order Dependency]: $lastN returns the last n values as ordered
# by the preceding $sort stage, preserving that order in the output array.
LASTN_SORT_ORDER_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "sort_ascending",
        docs=[{"_id": 0, "v": 30}, {"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 2, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [20, 30]}],
        msg="$lastN should return the highest values, in order, when sorted ascending",
    ),
    AccumulatorTestCase(
        "sort_descending",
        docs=[{"_id": 0, "v": 30}, {"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[
            {"$sort": {"v": -1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 2, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [20, 10]}],
        msg="$lastN should return the lowest values, in order, when sorted descending",
    ),
    AccumulatorTestCase(
        "sort_by_secondary_field",
        docs=[
            {"_id": 0, "s": 1, "v": "a"},
            {"_id": 1, "s": 3, "v": "c"},
            {"_id": 2, "s": 2, "v": "b"},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 2, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["b", "c"]}],
        msg="$lastN should return values from the documents with the highest sort keys",
    ),
    AccumulatorTestCase(
        "compound_sort",
        docs=[
            {"_id": 0, "cat": "A", "val": 1, "v": "a1"},
            {"_id": 1, "cat": "A", "val": 2, "v": "a2"},
            {"_id": 2, "cat": "B", "val": 1, "v": "b1"},
        ],
        pipeline=[
            {"$sort": {"cat": 1, "val": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 2, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ["a2", "b1"]}],
        msg="$lastN should return the last values by compound sort order",
    ),
]

# Property [Null and Missing Handling]: $lastN includes null and missing values
# (missing becomes null) rather than skipping them, unlike numeric accumulators.
LASTN_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_in_last_n",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": 20}, {"_id": 2, "v": None}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 2, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [20, None]}],
        msg="$lastN should include a null value present in the last n documents",
    ),
    AccumulatorTestCase(
        "missing_in_last_n",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": 20}, {"_id": 2}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 2, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [20, None]}],
        msg="$lastN should include a missing field in the last n documents as null",
    ),
    AccumulatorTestCase(
        "all_null",
        docs=[{"_id": 0, "v": None}, {"_id": 1, "v": None}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 2, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None, None]}],
        msg="$lastN should return all null values when every document is null",
    ),
    AccumulatorTestCase(
        "all_missing",
        docs=[{"_id": 0}, {"_id": 1}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 2, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [None, None]}],
        msg="$lastN should return nulls when every document is missing the field",
    ),
]

# Property [Mixed BSON Types]: $lastN performs no type checking and returns
# whatever values the last n documents hold, preserving type and order.
LASTN_MIXED_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mixed_types_preserved",
        docs=[
            {"_id": 0, "v": 1},
            {"_id": 1, "v": "hello"},
            {"_id": 2, "v": True},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 3, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, "hello", True]}],
        msg="$lastN should preserve mixed BSON types in the returned array",
    ),
    AccumulatorTestCase(
        "arrays_preserved",
        docs=[
            {"_id": 0, "v": [1, 2]},
            {"_id": 1, "v": [3, 4]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 2, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [[1, 2], [3, 4]]}],
        msg="$lastN should return array-valued elements without traversal",
    ),
    AccumulatorTestCase(
        "special_numerics_preserved",
        docs=[
            {"_id": 0, "v": FLOAT_NAN},
            {"_id": 1, "v": FLOAT_INFINITY},
            {"_id": 2, "v": Decimal128("NaN")},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 3, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [FLOAT_NAN, FLOAT_INFINITY, Decimal128("NaN")]}],
        msg="$lastN should pass through special numeric values unchanged",
    ),
]

# Property [Empty-Group Behavior]: $lastN produces no groups when no documents
# reach $group, whether the collection is empty or $match excluded them all.
LASTN_EMPTY_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "empty_collection",
        docs=[],
        pipeline=[
            {"$group": {"_id": None, "result": {"$lastN": {"n": 2, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[],
        msg="$lastN on an empty collection should produce no groups",
    ),
    AccumulatorTestCase(
        "all_documents_filtered_out",
        docs=[{"_id": 0, "cat": "A", "v": 10}, {"_id": 1, "cat": "B", "v": 20}],
        pipeline=[
            {"$match": {"cat": "Z"}},
            {"$group": {"_id": None, "result": {"$lastN": {"n": 2, "input": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[],
        msg="$lastN should produce no groups when every document is filtered out",
    ),
]

LASTN_SUCCESS_TESTS = (
    LASTN_N_VALUE_TESTS
    + LASTN_MULTIPLE_GROUP_TESTS
    + LASTN_SORT_ORDER_TESTS
    + LASTN_NULL_MISSING_TESTS
    + LASTN_MIXED_TYPE_TESTS
    + LASTN_EMPTY_GROUP_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LASTN_SUCCESS_TESTS))
def test_accumulator_lastN(collection, test_case: AccumulatorTestCase):
    """Test $lastN accumulator success cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccessNaN(result, test_case.expected, msg=test_case.msg)
