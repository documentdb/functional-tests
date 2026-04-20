"""
Edge case tests for $gte operator.

Covers deeply nested field paths with NaN, large array element matching,
empty string ordering, null/missing field handling, and BSON type bracketing.
"""

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
        filter={"a.b.c.d.e": {"$gte": 10}},
        doc=[
            {"_id": 1, "a": {"b": {"c": {"d": {"e": 5}}}}},
            {"_id": 2, "a": {"b": {"c": {"d": {"e": 15}}}}},
            {"_id": 3, "a": {"b": {"c": {"d": {"e": float("nan")}}}}},
        ],
        expected=[{"_id": 2, "a": {"b": {"c": {"d": {"e": 15}}}}}],
        msg="$gte on deeply nested field path; NaN does not satisfy $gte",
    ),
    QueryTestCase(
        id="large_array_element_match",
        filter={"a": {"$gte": 1001}},
        doc=[
            {"_id": 1, "a": list(range(0, 1000)) + [1001]},
            {"_id": 2, "a": list(range(0, 1000))},
        ],
        expected=[{"_id": 1, "a": list(range(0, 1000)) + [1001]}],
        msg="$gte matches element in a large (1001-element) array",
    ),
]

NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_query_matches_null_and_missing",
        filter={"a": {"$gte": None}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": None}, {"_id": 3}],
        expected=[{"_id": 2, "a": None}, {"_id": 3}],
        msg="$gte null matches null and missing fields (null >= null)",
    ),
    QueryTestCase(
        id="null_field_not_gte_numeric",
        filter={"a": {"$gte": 5}},
        doc=[{"_id": 1, "a": None}],
        expected=[],
        msg="null field does not match $gte with numeric query",
    ),
]

TYPE_BRACKETING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="gte_false_no_cross_type_int_zero",
        filter={"a": {"$gte": False}},
        doc=[{"_id": 1, "a": 0}],
        expected=[],
        msg="int 0 does not match $gte false (different BSON types)",
    ),
    QueryTestCase(
        id="gte_true_no_cross_type_int_one",
        filter={"a": {"$gte": True}},
        doc=[{"_id": 1, "a": 1}],
        expected=[],
        msg="int 1 does not match $gte true (different BSON types)",
    ),
    QueryTestCase(
        id="gte_int_zero_no_cross_type_false",
        filter={"a": {"$gte": 0}},
        doc=[{"_id": 1, "a": False}],
        expected=[],
        msg="false does not match $gte 0 (different BSON types)",
    ),
    QueryTestCase(
        id="gte_int_one_no_cross_type_true",
        filter={"a": {"$gte": 1}},
        doc=[{"_id": 1, "a": True}],
        expected=[],
        msg="true does not match $gte 1 (different BSON types)",
    ),
    QueryTestCase(
        id="gte_int_zero_no_cross_type_string",
        filter={"a": {"$gte": 0}},
        doc=[{"_id": 1, "a": "0"}],
        expected=[],
        msg="string '0' does not match $gte int 0 (different BSON types)",
    ),
    QueryTestCase(
        id="gte_string_no_cross_type_int",
        filter={"a": {"$gte": "0"}},
        doc=[{"_id": 1, "a": 0}],
        expected=[],
        msg="int 0 does not match $gte string '0' (different BSON types)",
    ),
    QueryTestCase(
        id="gte_null_no_cross_type_string",
        filter={"a": {"$gte": None}},
        doc=[{"_id": 1, "a": "hello"}],
        expected=[],
        msg="string does not match $gte null (different BSON types)",
    ),
    QueryTestCase(
        id="gte_false_no_cross_type_null",
        filter={"a": {"$gte": False}},
        doc=[{"_id": 1, "a": None}],
        expected=[],
        msg="null does not match $gte false (different BSON types)",
    ),
    QueryTestCase(
        id="gte_int_zero_no_cross_type_null",
        filter={"a": {"$gte": 0}},
        doc=[{"_id": 1, "a": None}],
        expected=[],
        msg="null does not match $gte int 0 (different BSON types)",
    ),
    QueryTestCase(
        id="gte_null_no_cross_type_bool",
        filter={"a": {"$gte": None}},
        doc=[{"_id": 1, "a": True}],
        expected=[],
        msg="bool true does not match $gte null (different BSON types)",
    ),
    QueryTestCase(
        id="bool_false_not_gte_true",
        filter={"a": {"$gte": True}},
        doc=[{"_id": 1, "a": False}],
        expected=[],
        msg="bool false does not match $gte true (false < true)",
    ),
]

ALL_PARAMETRIZED_TESTS = MISC_EDGE_CASE_TESTS + NULL_MISSING_TESTS + TYPE_BRACKETING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_PARAMETRIZED_TESTS))
def test_gte_edge_cases(collection, test):
    """Parametrized test for $gte edge cases.

    Covers nested fields, large arrays, null/missing, and type bracketing.
    """
    collection.insert_many(test.doc)
    cmd = {"find": collection.name, "filter": test.filter}
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, ignore_doc_order=True)
