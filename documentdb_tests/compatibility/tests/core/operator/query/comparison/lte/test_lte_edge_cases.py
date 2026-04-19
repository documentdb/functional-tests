"""
Edge case tests for $lte operator.

Covers deeply nested field paths with NaN, large array element matching,
empty string ordering, and null/missing field handling.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="deeply_nested_field_with_nan",
        filter={"a.b.c.d.e": {"$lte": 10}},
        doc=[
            {"_id": 1, "a": {"b": {"c": {"d": {"e": 5}}}}},
            {"_id": 2, "a": {"b": {"c": {"d": {"e": 15}}}}},
            {"_id": 3, "a": {"b": {"c": {"d": {"e": float("nan")}}}}},
        ],
        expected=[{"_id": 1, "a": {"b": {"c": {"d": {"e": 5}}}}}],
        msg="$lte on deeply nested field; NaN does not satisfy $lte",
    ),
    QueryTestCase(
        id="large_array_element_match",
        filter={"a": {"$lte": 0}},
        doc=[
            {"_id": 1, "a": list(range(1, 1001)) + [0]},
            {"_id": 2, "a": list(range(1, 1001))},
        ],
        expected=[{"_id": 1, "a": list(range(1, 1001)) + [0]}],
        msg="$lte matches element in a large (1001-element) array",
    ),
    QueryTestCase(
        id="empty_string_lte_itself",
        filter={"a": {"$lte": ""}},
        doc=[{"_id": 1, "a": ""}, {"_id": 2, "a": "a"}],
        expected=[{"_id": 1, "a": ""}],
        msg="empty string matches $lte for itself",
    ),
    QueryTestCase(
        id="null_query_matches_null_and_missing",
        filter={"a": {"$lte": None}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": None}, {"_id": 3}],
        expected=[{"_id": 2, "a": None}, {"_id": 3}],
        msg="$lte null matches null and missing fields (null <= null)",
    ),
    QueryTestCase(
        id="null_field_not_lte_numeric",
        filter={"a": {"$lte": 5}},
        doc=[{"_id": 1, "a": None}],
        expected=[],
        msg="null field does not match $lte with numeric query",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EDGE_CASE_TESTS))
def test_lte_edge_cases(collection, test):
    """Parametrized test for $lte edge cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
