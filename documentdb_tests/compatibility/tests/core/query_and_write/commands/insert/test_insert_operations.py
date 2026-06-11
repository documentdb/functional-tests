"""
Insert operation smoke tests.

Wiring-level tests confirming insert accepts flat, nested, and array-valued
documents and correctly rejects duplicate _id. Detailed type coverage is in
test_insert_bson_type_preservation.py; _id semantics are in
test_insert_id_handling.py.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import DUPLICATE_KEY_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class InsertTest(BaseTestCase):
    """Test case for insert operation wiring."""

    documents: Any = None
    expected_n: int = 1


# Property [Insert Acceptance]: insert accepts single and multiple documents with
# varying shapes — flat, nested, array-valued, and minimal — and reports the
# correct inserted count.
TESTS: list[InsertTest] = [
    InsertTest(
        "single_document",
        documents=[{"_id": 0, "a": "A", "b": 30}],
        expected_n=1,
        msg="insert should insert a single document.",
        marks=(pytest.mark.smoke,),
    ),
    InsertTest(
        "many_documents",
        documents=[
            {"_id": 0, "a": "A", "b": 30},
            {"_id": 1, "a": "B", "b": 25},
            {"_id": 2, "a": "C", "b": 35},
        ],
        expected_n=3,
        msg="insert should insert multiple documents.",
        marks=(pytest.mark.smoke,),
    ),
    InsertTest(
        "nested_document",
        documents=[{"_id": 0, "a": "A", "b": {"b1": 30, "b2": {"b3": "NYC"}}}],
        expected_n=1,
        msg="insert should accept a document with nested subdocuments.",
    ),
    InsertTest(
        "array_field",
        documents=[{"_id": 0, "a": "A", "b": ["python", "mongodb"], "c": [95, 87]}],
        expected_n=1,
        msg="insert should accept a document with array-valued fields.",
    ),
    InsertTest(
        "minimal_document",
        documents=[{"_id": 0}],
        expected_n=1,
        msg="insert should accept a document with only an _id field.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_insert_operations(collection, test: InsertTest):
    """Test insert accepts various document shapes."""
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": test.documents},
    )
    assertSuccessPartial(result, {"ok": 1.0, "n": test.expected_n}, msg=test.msg)


@pytest.mark.insert
def test_insert_duplicate_id_fails(collection):
    """Test that inserting a duplicate _id produces a duplicate key error."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": "dup", "a": "A"}]},
    )
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": "dup", "a": "B"}]},
    )
    assertFailureCode(result, DUPLICATE_KEY_ERROR, msg="insert should reject a duplicate _id.")
