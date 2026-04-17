"""
Tests for $nin core semantics.

Covers basic exclusion, equivalence with $not+$in, complement of $in,
single-element equivalence with $ne, absent field matching, and _id field targeting.
"""

import pytest
from bson import ObjectId

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

_oid1, _oid2, _oid3 = ObjectId(), ObjectId(), ObjectId()

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="basic_exclusion",
        filter={"a": {"$nin": [2, 4]}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 2},
            {"_id": 3, "a": 3},
            {"_id": 4, "a": 4},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 3, "a": 3}],
        msg="$nin excludes matching values and returns non-matching",
    ),
    QueryTestCase(
        id="no_matches_returns_all",
        filter={"a": {"$nin": [10, 20]}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 2},
            {"_id": 3, "a": 3},
        ],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 2},
            {"_id": 3, "a": 3},
        ],
        msg="$nin returns all docs when no values match",
    ),
    QueryTestCase(
        id="all_excluded_returns_none",
        filter={"a": {"$nin": [1, 2]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        expected=[],
        msg="$nin returns no docs when all values are excluded",
    ),
    QueryTestCase(
        id="nin_equivalent_to_not_in",
        filter={"a": {"$nin": [1, 2]}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 2},
            {"_id": 3, "a": 3},
            {"_id": 4, "a": None},
            {"_id": 5, "b": 1},
        ],
        expected=[
            {"_id": 3, "a": 3},
            {"_id": 4, "a": None},
            {"_id": 5, "b": 1},
        ],
        msg="$nin produces same results as $not+$in",
    ),
    QueryTestCase(
        id="not_nin_equivalent_to_in",
        filter={"a": {"$not": {"$nin": [1, 2]}}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 2},
            {"_id": 3, "a": 3},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        msg="$not+$nin is equivalent to $in",
    ),
    QueryTestCase(
        id="complement_of_in",
        filter={"a": {"$nin": [1, 3]}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 2},
            {"_id": 3, "a": 3},
            {"_id": 4, "a": 4},
            {"_id": 5, "a": 5},
        ],
        expected=[
            {"_id": 2, "a": 2},
            {"_id": 4, "a": 4},
            {"_id": 5, "a": 5},
        ],
        msg="$nin returns complement of $in",
    ),
    QueryTestCase(
        id="single_element_equivalent_to_ne",
        filter={"a": {"$nin": [1]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        expected=[{"_id": 2, "a": 2}],
        msg="$nin with single element is equivalent to $ne",
    ),
    QueryTestCase(
        id="matches_absent_field",
        filter={"a": {"$nin": [1]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "b": 1}],
        expected=[{"_id": 2, "b": 1}],
        msg="$nin matches documents where field is absent",
    ),
    QueryTestCase(
        id="on_id_with_integers",
        filter={"_id": {"$nin": [1, 3]}},
        doc=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        expected=[{"_id": 2}],
        msg="$nin on _id field with integer values",
    ),
    QueryTestCase(
        id="on_id_with_objectid",
        filter={"_id": {"$nin": [_oid1, _oid3]}},
        doc=[{"_id": _oid1}, {"_id": _oid2}, {"_id": _oid3}],
        expected=[{"_id": _oid2}],
        msg="$nin on _id field with ObjectId values",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TESTS))
def test_nin_core_semantics(collection, test_case):
    """Parametrized test for $nin core semantics."""
    collection.insert_many(test_case.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test_case.filter})
    assertSuccess(result, test_case.expected, ignore_doc_order=True)
