"""
Edge case tests for $lt operator.

Covers deeply nested field paths with NaN, large array element matching,
empty string ordering, null/missing field handling.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

_ARR_WITH_ZERO = list(range(1, 1001)) + [0]
_ARR_WITHOUT = list(range(1, 1001))

EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="deeply_nested_field_with_nan",
        filter={"a.b.c.d.e": {"$lt": 10}},
        doc=[
            {"_id": 1, "a": {"b": {"c": {"d": {"e": 5}}}}},
            {"_id": 2, "a": {"b": {"c": {"d": {"e": 15}}}}},
            {"_id": 3, "a": {"b": {"c": {"d": {"e": float("nan")}}}}},
        ],
        expected=[{"_id": 1, "a": {"b": {"c": {"d": {"e": 5}}}}}],
        msg="$lt on deeply nested field; NaN does not satisfy $lt",
    ),
    QueryTestCase(
        id="large_array_element_match",
        filter={"a": {"$lt": 1}},
        doc=[{"_id": 1, "a": _ARR_WITH_ZERO}, {"_id": 2, "a": _ARR_WITHOUT}],
        expected=[{"_id": 1, "a": _ARR_WITH_ZERO}],
        msg="$lt matches element in a large (1001-element) array",
    ),
    QueryTestCase(
        id="empty_string_lt_nonempty",
        filter={"a": {"$lt": "a"}},
        doc=[{"_id": 1, "a": ""}, {"_id": 2, "a": "b"}],
        expected=[{"_id": 1, "a": ""}],
        msg="empty string is less than any non-empty string",
    ),
    QueryTestCase(
        id="null_query_no_match",
        filter={"a": {"$lt": None}},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": None}, {"_id": 3}],
        expected=[],
        msg="$lt null returns no documents",
    ),
    QueryTestCase(
        id="null_field_not_lt_numeric",
        filter={"a": {"$lt": 5}},
        doc=[{"_id": 1, "a": None}],
        expected=[],
        msg="null field does not match $lt with numeric query",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EDGE_CASE_TESTS))
def test_lt_edge_cases(collection, test):
    """Parametrized test for $lt edge cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
