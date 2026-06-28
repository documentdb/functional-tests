"""Tests for $mergeObjects accumulator: null/missing handling."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null Ignored]: null values are silently ignored by $mergeObjects,
# contributing nothing to the merged result.
MERGE_OBJECTS_NULL_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_all",
        docs=[{"s": 1, "v": None}, {"s": 2, "v": None}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should return empty document when all values are null",
    ),
    AccumulatorTestCase(
        "null_single",
        docs=[{"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should return empty document for a single null value",
    ),
    AccumulatorTestCase(
        "null_with_object",
        docs=[{"s": 1, "v": None}, {"s": 2, "v": {"a": 1}}, {"s": 3, "v": {"b": 2}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should ignore null and merge remaining objects",
    ),
    AccumulatorTestCase(
        "null_first",
        docs=[{"s": 1, "v": None}, {"s": 2, "v": {"a": 1}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1}}],
        msg="$mergeObjects should ignore null in first position",
    ),
    AccumulatorTestCase(
        "null_last",
        docs=[{"s": 1, "v": {"a": 1}}, {"s": 2, "v": None}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1}}],
        msg="$mergeObjects should ignore null in last position",
    ),
    AccumulatorTestCase(
        "null_middle",
        docs=[{"s": 1, "v": {"a": 1}}, {"s": 2, "v": None}, {"s": 3, "v": {"b": 2}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should ignore null in middle position",
    ),
    AccumulatorTestCase(
        "null_multiple_interspersed",
        docs=[
            {"s": 1, "v": None},
            {"s": 2, "v": {"a": 1}},
            {"s": 3, "v": None},
            {"s": 4, "v": {"b": 2}},
            {"s": 5, "v": None},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should ignore multiple interspersed nulls",
    ),
]

# Property [Missing Ignored]: missing fields are silently ignored by
# $mergeObjects, contributing nothing to the merged result.
MERGE_OBJECTS_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "missing_all",
        docs=[{"s": 1, "x": 1}, {"s": 2, "x": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should return empty document when all documents have missing field",
    ),
    AccumulatorTestCase(
        "missing_single",
        docs=[{"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should return empty document for a single missing field",
    ),
    AccumulatorTestCase(
        "missing_with_object",
        docs=[{"s": 1, "x": 1}, {"s": 2, "v": {"a": 1}}, {"s": 3, "v": {"b": 2}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should ignore missing and merge remaining objects",
    ),
    AccumulatorTestCase(
        "missing_first",
        docs=[{"s": 1, "x": 1}, {"s": 2, "v": {"a": 1}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1}}],
        msg="$mergeObjects should ignore missing field in first document",
    ),
    AccumulatorTestCase(
        "missing_last",
        docs=[{"s": 1, "v": {"a": 1}}, {"s": 2, "x": 1}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1}}],
        msg="$mergeObjects should ignore missing field in last document",
    ),
]

# Property [Null and Missing Mixed]: null and missing values are both ignored
# when mixed together, with objects being merged normally.
MERGE_OBJECTS_NULL_MISSING_MIX_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_and_missing_mix",
        docs=[{"s": 1, "v": None}, {"s": 2, "x": 1}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should return empty document when group has only null and missing",
    ),
    AccumulatorTestCase(
        "null_and_missing_with_object",
        docs=[{"s": 1, "v": None}, {"s": 2, "x": 1}, {"s": 3, "v": {"a": 1}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1}}],
        msg="$mergeObjects should ignore both null and missing, merging only objects",
    ),
    AccumulatorTestCase(
        "null_and_missing_multi_group",
        docs=[
            {"s": 1, "cat": "A", "v": None},
            {"s": 2, "cat": "A", "v": {"a": 1}},
            {"s": 3, "cat": "B"},
            {"s": 4, "cat": "B", "v": {"b": 2}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": "$cat", "result": {"$mergeObjects": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": {"a": 1}},
            {"_id": "B", "result": {"b": 2}},
        ],
        msg="$mergeObjects should handle null and missing independently per group boundary",
    ),
]

# Property [$$REMOVE Handling]: $$REMOVE is treated as missing and silently
# ignored by $mergeObjects.
MERGE_OBJECTS_REMOVE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "remove_only",
        docs=[{"v": {"a": 1}}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$mergeObjects": {"$cond": [False, "$v", "$$REMOVE"]}},
                }
            }
        ],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should treat $$REMOVE as missing and return empty document",
    ),
    AccumulatorTestCase(
        "remove_with_object",
        docs=[
            {"s": 1, "v": {"a": 1}, "flag": True},
            {"s": 2, "v": {"b": 2}, "flag": False},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$mergeObjects": {"$cond": ["$flag", "$v", "$$REMOVE"]}},
                }
            },
        ],
        expected=[{"_id": None, "result": {"a": 1}}],
        msg="$mergeObjects should ignore $$REMOVE and merge only non-removed objects",
    ),
]

# Property [Constant Null]: a constant null expression produces an empty
# document result.
MERGE_OBJECTS_CONSTANT_NULL_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "constant_null",
        docs=[{"s": 1, "x": 1}, {"s": 2, "x": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": None}}},
        ],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should return empty document for a constant null expression",
    ),
    AccumulatorTestCase(
        "literal_null_expr",
        docs=[{"s": 1, "x": 1}, {"s": 2, "x": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": {"$literal": None}}}},
        ],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should return empty document when expression evaluates to null",
    ),
]

# Property [Empty Collection]: empty collection produces no group output
# (empty result set).
MERGE_OBJECTS_EMPTY_COLLECTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "empty_collection",
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": "$v"}}}],
        expected=[],
        msg="$mergeObjects on empty collection should return empty result set",
    ),
]

MERGE_OBJECTS_NULL_MISSING_TESTS = (
    MERGE_OBJECTS_NULL_TESTS
    + MERGE_OBJECTS_MISSING_TESTS
    + MERGE_OBJECTS_NULL_MISSING_MIX_TESTS
    + MERGE_OBJECTS_REMOVE_TESTS
    + MERGE_OBJECTS_CONSTANT_NULL_TESTS
    + MERGE_OBJECTS_EMPTY_COLLECTION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MERGE_OBJECTS_NULL_MISSING_TESTS))
def test_accumulator_mergeObjects_null_missing(collection, test_case: AccumulatorTestCase):
    """Test $mergeObjects null/missing handling."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
    actual_docs = result["cursor"]["firstBatch"]
    for actual, exp in zip(actual_docs, test_case.expected):
        if "result" in exp and isinstance(exp["result"], dict):
            actual_keys = list(actual["result"].keys())
            expected_keys = list(exp["result"].keys())
            if actual_keys != expected_keys:
                raise AssertionError(
                    f"[KEY_ORDER_MISMATCH] {test_case.msg}\n"
                    f"Expected key order: {expected_keys}\n"
                    f"Actual key order:   {actual_keys}"
                )
