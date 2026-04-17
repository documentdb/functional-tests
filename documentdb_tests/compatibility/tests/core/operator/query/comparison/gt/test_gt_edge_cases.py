"""
Edge case tests for $gt operator.

Covers deeply nested field paths with NaN, large array element matching,
empty string ordering, null/missing field handling, and cross-type bracketing.
"""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

MISC_EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="deeply_nested_field_with_nan",
        filter={"a.b.c.d.e": {"$gt": 10}},
        doc=[
            {"_id": 1, "a": {"b": {"c": {"d": {"e": 5}}}}},
            {"_id": 2, "a": {"b": {"c": {"d": {"e": 15}}}}},
            {"_id": 3, "a": {"b": {"c": {"d": {"e": float("nan")}}}}},
        ],
        expected=[{"_id": 2, "a": {"b": {"c": {"d": {"e": 15}}}}}],
        msg="$gt on deeply nested field path; NaN does not satisfy $gt",
    ),
    QueryTestCase(
        id="large_array_element_match",
        filter={"a": {"$gt": 1000}},
        doc=[
            {"_id": 1, "a": list(range(0, 1000)) + [1001]},
            {"_id": 2, "a": list(range(0, 1000))},
        ],
        expected=[{"_id": 1, "a": list(range(0, 1000)) + [1001]}],
        msg="$gt matches element in a large (1001-element) array",
    ),
    QueryTestCase(
        id="empty_string_gt_nothing",
        filter={"a": {"$gt": ""}},
        doc=[{"_id": 1, "a": ""}, {"_id": 2, "a": "a"}],
        expected=[{"_id": 2, "a": "a"}],
        msg="non-empty string is greater than empty string",
    ),
]

NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="gt_null_query_returns_nothing",
        filter={"a": {"$gt": None}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": None}, {"_id": 3}],
        expected=[],
        msg="$gt null returns no documents",
    ),
    QueryTestCase(
        id="null_field_not_gt_numeric_query",
        filter={"a": {"$gt": 5}},
        doc=[{"_id": 1, "a": None}],
        expected=[],
        msg="null field does not match $gt with numeric query",
    ),
    QueryTestCase(
        id="missing_field_not_gt_numeric_query",
        filter={"a": {"$gt": 5}},
        doc=[{"_id": 1, "b": 10}],
        expected=[],
        msg="missing field does not match $gt numeric query",
    ),
    QueryTestCase(
        id="gt_null_on_missing_field_no_match",
        filter={"a": {"$gt": None}},
        doc=[{"_id": 1, "b": 10}],
        expected=[],
        msg="$gt null on missing field returns no match",
    ),
    QueryTestCase(
        id="gt_null_on_non_null_field_no_match",
        filter={"a": {"$gt": None}},
        doc=[{"_id": 1, "a": 5}],
        expected=[],
        msg="$gt null on non-null field returns no match (type bracketing)",
    ),
]

TYPE_BRACKETING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="bool_false_field_not_gt_int_0_query",
        filter={"a": {"$gt": 0}},
        doc=[{"_id": 1, "a": False}],
        expected=[],
        msg="boolean false is not > int 0 (different type brackets)",
    ),
    QueryTestCase(
        id="bool_true_field_not_gt_int_1_query",
        filter={"a": {"$gt": 1}},
        doc=[{"_id": 1, "a": True}],
        expected=[],
        msg="boolean true is not > int 1 (different type brackets)",
    ),
    QueryTestCase(
        id="date_field_not_gt_numeric_query",
        filter={"a": {"$gt": 0}},
        doc=[{"_id": 1, "a": datetime(2025, 1, 1, tzinfo=timezone.utc)}],
        expected=[],
        msg="date field does not match $gt numeric query (different type brackets)",
    ),
    QueryTestCase(
        id="null_field_not_gt_string_query",
        filter={"a": {"$gt": "abc"}},
        doc=[{"_id": 1, "a": None}],
        expected=[],
        msg="null field does not match $gt string query (different type brackets)",
    ),
    QueryTestCase(
        id="object_not_gt_null",
        filter={"a": {"$gt": None}},
        doc=[{"_id": 1, "a": {}}],
        expected=[],
        msg="empty object does not match $gt null (different BSON types)",
    ),
]

ALL_PARAMETRIZED_TESTS = MISC_EDGE_CASE_TESTS + NULL_MISSING_TESTS + TYPE_BRACKETING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_PARAMETRIZED_TESTS))
def test_gt_edge_cases(collection, test):
    """Parametrized test for $gt edge cases.

    Covers nested fields, large arrays, null/missing, and type bracketing.
    """
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
