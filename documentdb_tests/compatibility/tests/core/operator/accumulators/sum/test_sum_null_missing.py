"""Tests for $sum accumulator: null/missing handling and non-numeric type behavior."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null and Missing Behavior]: null and missing values are ignored by
# $sum, producing 0 (int32) when no numeric values remain.
SUM_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_all",
        docs=[{"v": None}, {"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=0,
        msg="$sum should return 0 when all values are null",
    ),
    AccumulatorTestCase(
        "missing_all",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=0,
        msg="$sum should return 0 when all documents have missing field",
    ),
    AccumulatorTestCase(
        "null_and_missing_mix",
        docs=[{"v": None}, {"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=0,
        msg="$sum should return 0 when group has only null and missing values",
    ),
    AccumulatorTestCase(
        "null_with_numeric",
        docs=[{"v": None}, {"v": 5}, {"v": 3}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=8,
        msg="$sum should ignore null and sum only numeric values",
    ),
    AccumulatorTestCase(
        "missing_with_numeric",
        docs=[{"x": 1}, {"v": 7}, {"v": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=9,
        msg="$sum should ignore missing and sum only numeric values",
    ),
    AccumulatorTestCase(
        "null_and_missing_with_numeric",
        docs=[{"v": None}, {"x": 1}, {"v": 10}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=10,
        msg="$sum should ignore both null and missing, summing only numeric values",
    ),
    AccumulatorTestCase(
        "constant_null",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": None}}}],
        expected=0,
        msg="$sum should return 0 for a constant null expression",
    ),
    AccumulatorTestCase(
        "literal_null_expr",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$literal": None}}}}],
        expected=0,
        msg="$sum should return 0 when expression evaluates to null",
    ),
    AccumulatorTestCase(
        "remove_only",
        docs=[{"v": 5}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$cond": [False, 1, "$$REMOVE"]}}}}],
        expected=0,
        msg="$sum should treat $$REMOVE as missing and return 0",
    ),
]

# Property [Non-Numeric Type Handling]: non-numeric BSON types are silently
# ignored by $sum, contributing nothing to the result.
SUM_NON_NUMERIC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "non_numeric_string_ignored",
        docs=[{"v": "hello"}, {"v": 10}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=10,
        msg="$sum should ignore string values and sum only numeric values",
    ),
    AccumulatorTestCase(
        "non_numeric_bool_true_ignored",
        docs=[{"v": True}, {"v": 7}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=7,
        msg="$sum should ignore boolean True (not coerce to 1)",
    ),
    AccumulatorTestCase(
        "non_numeric_bool_false_ignored",
        docs=[{"v": False}, {"v": 3}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=3,
        msg="$sum should ignore boolean False (not coerce to 0)",
    ),
    AccumulatorTestCase(
        "non_numeric_array_ignored",
        docs=[{"v": ["a", "b"]}, {"v": 4}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=4,
        msg="$sum should ignore array values",
    ),
    AccumulatorTestCase(
        "non_numeric_object_ignored",
        docs=[{"v": {"a": 1}}, {"v": 6}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=6,
        msg="$sum should ignore embedded object values",
    ),
    AccumulatorTestCase(
        "non_numeric_empty_object_ignored",
        docs=[{"v": {}}, {"v": 4}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=4,
        msg="$sum should ignore empty document values",
    ),
    AccumulatorTestCase(
        "non_numeric_objectid_ignored",
        docs=[{"v": ObjectId()}, {"v": 8}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=8,
        msg="$sum should ignore ObjectId values",
    ),
    AccumulatorTestCase(
        "non_numeric_datetime_ignored",
        docs=[{"v": datetime(2023, 1, 1, tzinfo=timezone.utc)}, {"v": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=2,
        msg="$sum should ignore datetime values",
    ),
    AccumulatorTestCase(
        "non_numeric_timestamp_ignored",
        docs=[{"v": Timestamp(1, 1)}, {"v": 9}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=9,
        msg="$sum should ignore Timestamp values",
    ),
    AccumulatorTestCase(
        "non_numeric_binary_ignored",
        docs=[{"v": Binary(b"\x01\x02")}, {"v": 5}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=5,
        msg="$sum should ignore Binary values",
    ),
    AccumulatorTestCase(
        "non_numeric_regex_ignored",
        docs=[{"v": Regex("abc", "i")}, {"v": 11}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=11,
        msg="$sum should ignore Regex values",
    ),
    AccumulatorTestCase(
        "non_numeric_code_ignored",
        docs=[{"v": Code("function(){}")}, {"v": 12}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=12,
        msg="$sum should ignore Code values",
    ),
    AccumulatorTestCase(
        "non_numeric_minkey_ignored",
        docs=[{"v": MinKey()}, {"v": 14}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=14,
        msg="$sum should ignore MinKey values",
    ),
    AccumulatorTestCase(
        "non_numeric_maxkey_ignored",
        docs=[{"v": MaxKey()}, {"v": 15}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=15,
        msg="$sum should ignore MaxKey values",
    ),
    AccumulatorTestCase(
        "non_numeric_all_non_numeric",
        docs=[{"v": "abc"}, {"v": True}, {"v": [1]}, {"v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=0,
        msg="$sum should return 0 when all values in a group are non-numeric",
    ),
    AccumulatorTestCase(
        "non_numeric_numeric_string_not_coerced",
        docs=[{"v": "123"}, {"v": 5}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=5,
        msg="$sum should not coerce numeric strings to numbers",
    ),
    AccumulatorTestCase(
        "non_numeric_array_single_element",
        docs=[{"v": [5]}, {"v": 10}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=10,
        msg="$sum should treat single-element numeric array as non-numeric",
    ),
    AccumulatorTestCase(
        "non_numeric_array_empty",
        docs=[{"v": []}, {"v": 7}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=7,
        msg="$sum should treat empty array as non-numeric",
    ),
    AccumulatorTestCase(
        "non_numeric_array_nested",
        docs=[{"v": [[1, 2]]}, {"v": 3}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=3,
        msg="$sum should treat nested array as non-numeric",
    ),
    AccumulatorTestCase(
        "non_numeric_array_of_numbers",
        docs=[{"v": [1, 2, 3]}, {"v": 20}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
        expected=20,
        msg="$sum should treat array of numbers as non-numeric in accumulator context",
    ),
    AccumulatorTestCase(
        "non_numeric_array_from_expression",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$literal": [1, 2, 3]}}}}],
        expected=0,
        msg="$sum should treat array expressions as non-numeric",
    ),
]

SUM_NULL_MISSING_AND_NON_NUMERIC_TESTS = SUM_NULL_MISSING_TESTS + SUM_NON_NUMERIC_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SUM_NULL_MISSING_AND_NON_NUMERIC_TESTS))
def test_sum_null_missing(collection, test_case: AccumulatorTestCase):
    """Test $sum null/missing handling and non-numeric type behavior."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(
        result,
        [{"_id": None, "result": test_case.expected}],
        msg=test_case.msg,
    )


# Property [Empty Collection]: empty collection produces no group output
# (empty result set).
def test_sum_empty_collection(collection):
    """Test $sum on empty collection returns empty result set."""
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": None, "result": {"$sum": "$v"}}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [], msg="$sum on empty collection should return empty result set")
