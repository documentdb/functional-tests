"""Tests for $push accumulator: null/missing handling and empty collection behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null Handling]: $push includes explicit null values in the output
# array, producing an array containing null for each document with a null value.
PUSH_NULL_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_all",
        docs=[{"v": None}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [None, None]}],
        msg="$push should include all null values in the output array",
    ),
    AccumulatorTestCase(
        "null_with_values",
        docs=[{"v": None}, {"v": 5}, {"v": 3}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [None, 3, 5]}],
        msg="$push should include null alongside other values in the array",
    ),
    AccumulatorTestCase(
        "null_constant",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": None}}},
        ],
        expected=[{"_id": None, "result": [None, None]}],
        msg="$push should produce array of nulls for constant null expression",
    ),
    AccumulatorTestCase(
        "null_literal",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": {"$literal": None}}}},
        ],
        expected=[{"_id": None, "result": [None, None]}],
        msg="$push should produce array of nulls for $literal null expression",
    ),
]

# Property [Missing Field Handling]: $push excludes values from documents where
# the referenced field is missing, producing a shorter array or an empty array
# if all documents lack the field.
PUSH_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "missing_all",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": []}],
        msg="$push should produce empty array when all documents are missing the field",
    ),
    AccumulatorTestCase(
        "missing_some",
        docs=[{"v": 10}, {"x": 1}, {"v": 20}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [10, 20]}],
        msg="$push should exclude missing values and collect only present values",
    ),
    AccumulatorTestCase(
        "missing_and_null_mix",
        docs=[{"v": None}, {"x": 1}, {"v": 10}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [None, 10]}],
        msg="$push should include null but exclude missing values",
    ),
]

# Property [$$REMOVE Handling]: $push treats $$REMOVE as a missing value,
# excluding it from the output array.
PUSH_REMOVE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "remove_all",
        docs=[{"v": 5}, {"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": {"$cond": [False, "$v", "$$REMOVE"]}}}},
        ],
        expected=[{"_id": None, "result": []}],
        msg="$push should treat $$REMOVE as missing and exclude from array",
    ),
    AccumulatorTestCase(
        "remove_some",
        docs=[{"v": 5, "keep": True}, {"v": 10, "keep": False}, {"v": 15, "keep": True}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$push": {"$cond": ["$keep", "$v", "$$REMOVE"]}}}},
        ],
        expected=[{"_id": None, "result": [5, 15]}],
        msg="$push should include values where $cond returns the value and exclude $$REMOVE",
    ),
]

# Property [Empty Collection]: empty collection produces no group output
# (empty result set).
PUSH_EMPTY_COLLECTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "empty_collection",
        docs=None,
        pipeline=[{"$group": {"_id": None, "result": {"$push": "$v"}}}],
        expected=[],
        msg="$push on empty collection should return empty result set",
    ),
]

# Property [Multiple $push in Single $group]: multiple $push accumulators in
# the same $group independently handle null/missing per field across groups.
PUSH_MULTI_ACCUMULATOR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multi_push_null_missing_per_field",
        docs=[
            {"cat": "A", "x": 1, "y": None, "s": 1},
            {"cat": "A", "x": None, "s": 2},
            {"cat": "A", "y": 3, "s": 3},
            {"cat": "B", "x": 10, "y": 20, "s": 4},
            {"cat": "B", "y": 30, "s": 5},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "xs": {"$push": "$x"},
                    "ys": {"$push": "$y"},
                }
            },
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "xs": [1, None], "ys": [None, 3]},
            {"_id": "B", "xs": [10], "ys": [20, 30]},
        ],
        msg="Multiple $push should independently handle null/missing per field across groups",
    ),
]

# Property [Multiple $group Stages]: $push correctly collects values when
# multiple $group stages appear in the same pipeline, with each stage
# performing actual grouping (not just _id: null).
PUSH_MULTI_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multi_group_reaggregate",
        docs=[
            {"region": "us", "dept": "eng", "v": 1},
            {"region": "us", "dept": "eng", "v": 2},
            {"region": "us", "dept": "sales", "v": 3},
            {"region": "eu", "dept": "eng", "v": 4},
            {"region": "eu", "dept": "eng", "v": 5},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": "$dept", "values": {"$push": "$v"}}},
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "depts": {"$push": "$_id"},
                    "all_values": {"$push": "$values"},
                }
            },
        ],
        expected=[
            {
                "_id": None,
                "depts": ["eng", "sales"],
                "all_values": [[1, 2, 4, 5], [3]],
            }
        ],
        msg="Chained $group stages should each produce correct $push results",
    ),
    AccumulatorTestCase(
        "multi_group_with_null_propagation",
        docs=[
            {"cat": "A", "sub": "x", "v": 1},
            {"cat": "A", "sub": "x", "v": None},
            {"cat": "A", "sub": "y", "v": 3},
            {"cat": "B", "sub": "x"},
            {"cat": "B", "sub": "y", "v": 5},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": {"cat": "$cat", "sub": "$sub"}, "vals": {"$push": "$v"}}},
            {"$sort": {"_id.cat": 1, "_id.sub": 1}},
            {
                "$group": {
                    "_id": "$_id.cat",
                    "sub_groups": {"$push": "$_id.sub"},
                    "sub_vals": {"$push": "$vals"},
                }
            },
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {
                "_id": "A",
                "sub_groups": ["x", "y"],
                "sub_vals": [[None, 1], [3]],
            },
            {
                "_id": "B",
                "sub_groups": ["x", "y"],
                "sub_vals": [[], [5]],
            },
        ],
        msg="Chained $group stages should propagate null/missing through $push correctly",
    ),
]

PUSH_NULL_MISSING_TESTS = (
    PUSH_NULL_TESTS
    + PUSH_MISSING_TESTS
    + PUSH_REMOVE_TESTS
    + PUSH_EMPTY_COLLECTION_TESTS
    + PUSH_MULTI_ACCUMULATOR_TESTS
    + PUSH_MULTI_GROUP_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(PUSH_NULL_MISSING_TESTS))
def test_push_null_missing(collection, test_case: AccumulatorTestCase):
    """Test $push null and missing handling."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
