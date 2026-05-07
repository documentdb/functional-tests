"""
Tests for implicit AND vs explicit $and equivalence.

Tests that comma-separated query expressions produce the same results
as explicit $and, and that explicit $and is required for duplicate keys.
"""

import pytest
from bson import SON

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [
    {"_id": 1, "a": 1, "b": 2, "price": 7.99},
    {"_id": 2, "a": 1, "b": 3, "price": 3.99},
    {"_id": 3, "a": 2, "b": 2, "price": 4.99},
]

ALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="implicit_comma_separated",
        filter={"a": 1, "b": 2},
        doc=DOCS,
        expected=[{"_id": 1, "a": 1, "b": 2, "price": 7.99}],
        msg="Implicit AND matches docs satisfying both conditions",
    ),
    QueryTestCase(
        id="explicit_equivalent_to_implicit",
        filter={"$and": [{"a": 1}, {"b": 2}]},
        doc=DOCS,
        expected=[{"_id": 1, "a": 1, "b": 2, "price": 7.99}],
        msg="Explicit $and matches same as implicit AND",
    ),
    QueryTestCase(
        id="implicit_multiple_conditions_same_field",
        filter={"price": {"$ne": 7.99, "$exists": True}},
        doc=DOCS,
        expected=[
            {"_id": 2, "a": 1, "b": 3, "price": 3.99},
            {"_id": 3, "a": 2, "b": 2, "price": 4.99},
        ],
        msg="Implicit AND on same field works",
    ),
    QueryTestCase(
        id="explicit_multiple_conditions_same_field",
        filter={"$and": [{"price": {"$ne": 7.99}}, {"price": {"$exists": True}}]},
        doc=DOCS,
        expected=[
            {"_id": 2, "a": 1, "b": 3, "price": 3.99},
            {"_id": 3, "a": 2, "b": 2, "price": 4.99},
        ],
        msg="Explicit $and on same field works",
    ),
    QueryTestCase(
        id="explicit_required_duplicate_keys",
        filter={"$and": [{"price": {"$in": [7.99, 3.99]}}, {"price": {"$in": [4.99, 3.99]}}]},
        doc=DOCS,
        expected=[{"_id": 2, "a": 1, "b": 3, "price": 3.99}],
        msg="Explicit $and with duplicate keys intersects correctly",
    ),
    QueryTestCase(
        id="implicit_duplicate_key_uses_last",
        filter=SON([("price", {"$gt": 5}), ("price", {"$lt": 5})]),
        doc=DOCS,
        expected=[
            {"_id": 2, "a": 1, "b": 3, "price": 3.99},
            {"_id": 3, "a": 2, "b": 2, "price": 4.99},
        ],
        msg="Duplicate keys use last value, not AND semantics",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_and_implicit_equivalence(collection, test):
    """Test implicit AND vs explicit $and equivalence."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
