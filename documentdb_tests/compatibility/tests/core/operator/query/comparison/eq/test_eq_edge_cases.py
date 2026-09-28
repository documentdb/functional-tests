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
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_NAN

_OID = ObjectId("507f1f77bcf86cd799439011")

_DEEPLY_NESTED_DOC: dict = {"level": 1}
for _ in range(2, 11):
    _DEEPLY_NESTED_DOC = {"level": _DEEPLY_NESTED_DOC}

_LARGE_ARRAY = list(range(1000))

# Property [Structural Edge Cases]: $eq matches oversized and deeply structured
# operands exactly — an ObjectId _id, a 10-level nested document, and a
# 1000-element array.
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


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_eq_edge_cases(collection, test):
    """Parametrized test for $eq edge cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)


# Property [NaN Self-Equality]: $eq NaN on a dotted subdocument path matches the
# stored NaN document and nothing else.
def test_eq_subdocument_nan(collection):
    """Test $eq with NaN on a dotted subdocument path matches only the NaN document.

    Projects _id only: the behavior under test is which documents match, and
    projecting away the NaN payload keeps the comparison on plain equality.
    """
    collection.insert_many([{"_id": 1, "a": {"b": FLOAT_NAN}}, {"_id": 2, "a": {"b": 1}}])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"a.b": {"$eq": FLOAT_NAN}},
            "projection": {"_id": 1},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1}],
        msg="$eq on subdocument with NaN matches only NaN document",
        ignore_doc_order=True,
    )
