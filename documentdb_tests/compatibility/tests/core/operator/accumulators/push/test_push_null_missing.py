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

PUSH_NULL_MISSING_TESTS = PUSH_NULL_TESTS + PUSH_MISSING_TESTS + PUSH_REMOVE_TESTS


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


# Property [Empty Collection]: empty collection produces no group output
# (empty result set).
def test_push_empty_collection(collection):
    """Test $push on empty collection returns empty result set."""
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": None, "result": {"$push": "$v"}}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [], msg="$push on empty collection should return empty result set")
