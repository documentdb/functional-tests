"""
Edge case tests for $eq operator.

Covers ObjectId on _id, deeply nested documents, large arrays, and NaN on a
subdocument path.
"""

import pytest
from bson import ObjectId

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_NAN

_OID = ObjectId("507f1f77bcf86cd799439011")

_DEEPLY_NESTED_DOC: dict = {"level": 1}
for _ in range(2, 11):
    _DEEPLY_NESTED_DOC = {"level": _DEEPLY_NESTED_DOC}

_LARGE_ARRAY = list(range(1000))

TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="id_objectid",
        filter={"_id": {"$eq": _OID}},
        doc=[{"_id": _OID, "a": 1}, {"_id": ObjectId(), "a": 2}],
        expected=[{"_id": _OID, "a": 1}],
        msg="$eq on _id with ObjectId",
    ),
    QueryTestCase(
        id="deeply_nested_document",
        filter={"a": {"$eq": _DEEPLY_NESTED_DOC}},
        doc=[{"_id": 1, "a": _DEEPLY_NESTED_DOC}, {"_id": 2, "a": {"x": 1}}],
        expected=[{"_id": 1, "a": _DEEPLY_NESTED_DOC}],
        msg="$eq with deeply nested document matches",
    ),
    QueryTestCase(
        id="large_array",
        filter={"a": {"$eq": _LARGE_ARRAY}},
        doc=[{"_id": 1, "a": _LARGE_ARRAY}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 1, "a": _LARGE_ARRAY}],
        msg="$eq with large array matches same array",
    ),
]

NAN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="subdocument_nan",
        filter={"a.b": {"$eq": FLOAT_NAN}},
        doc=[{"_id": 1, "a": {"b": FLOAT_NAN}}, {"_id": 2, "a": {"b": 1}}],
        expected=[{"_id": 1, "a": {"b": FLOAT_NAN}}],
        msg="$eq on subdocument with NaN matches only NaN document",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_eq_edge_cases(collection, test):
    """Parametrized test for $eq edge cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)


@pytest.mark.parametrize("test", pytest_params(NAN_TESTS))
def test_eq_edge_cases_nan(collection, test):
    """Parametrized test for $eq edge cases involving NaN."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccessNaN(result, test.expected, ignore_doc_order=True)
